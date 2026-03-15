use std::sync::Mutex;

use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use tauri::State;

use crate::backend::BackendProcess;
use crate::error::Result;

static CLIENT: std::sync::OnceLock<Client> = std::sync::OnceLock::new();

fn get_client() -> &'static Client {
    CLIENT.get_or_init(|| Client::new())
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ProxyRequest {
    pub method: String,
    pub path: String,
    pub body: Option<Value>,
    pub query: Option<Value>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ProxyResponse {
    pub status: u16,
    pub body: Value,
}

#[tauri::command]
pub async fn proxy_request(
    request: ProxyRequest,
    backend: State<'_, Mutex<BackendProcess>>,
) -> Result<ProxyResponse> {
    let port = {
        let process = backend.lock().map_err(|e| e.to_string())?;
        process.port()
    };

    let client = get_client();
    let url = format!("http://127.0.0.1:{}{}", port, request.path);

    let response = match request.method.to_uppercase().as_str() {
        "GET" => {
            let mut req = client.get(&url);
            if let Some(query) = request.query {
                req = req.query(&query);
            }
            req.send().await
        }
        "POST" => {
            client
                .post(&url)
                .json(&request.body)
                .send()
                .await
        }
        "PUT" => {
            client
                .put(&url)
                .json(&request.body)
                .send()
                .await
        }
        "DELETE" => {
            client.delete(&url).send().await
        }
        _ => {
            return Err(format!("Unsupported HTTP method: {}", request.method).into());
        }
    }
    .map_err(|e| format!("Request failed: {}", e))?;

    let status = response.status().as_u16();
    let body = response
        .json()
        .await
        .unwrap_or_else(|_| Value::Null);

    Ok(ProxyResponse { status, body })
}
