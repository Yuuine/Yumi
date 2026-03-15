use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use tauri::State;

use crate::backend::BackendProcess;
use crate::error::Result;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BackendStatus {
    pub running: bool,
    pub port: u16,
}

#[tauri::command]
pub async fn start_backend(
    backend: State<'_, Mutex<BackendProcess>>,
) -> Result<BackendStatus> {
    let mut process = backend.lock().map_err(|e| e.to_string())?;
    process.start()?;
    
    Ok(BackendStatus {
        running: process.is_running(),
        port: process.port(),
    })
}

#[tauri::command]
pub async fn stop_backend(
    backend: State<'_, Mutex<BackendProcess>>,
) -> Result<BackendStatus> {
    let mut process = backend.lock().map_err(|e| e.to_string())?;
    process.stop()?;
    
    Ok(BackendStatus {
        running: process.is_running(),
        port: process.port(),
    })
}

#[tauri::command]
pub async fn get_backend_status(
    backend: State<'_, Mutex<BackendProcess>>,
) -> Result<BackendStatus> {
    let process = backend.lock().map_err(|e| e.to_string())?;
    
    Ok(BackendStatus {
        running: process.is_running(),
        port: process.port(),
    })
}
