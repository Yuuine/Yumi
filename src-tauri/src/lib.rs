mod backend;
mod commands;
mod error;
mod tray;

use std::sync::Mutex;
use tauri::Manager;

use crate::backend::BackendProcess;
use crate::commands::backend::*;
use crate::commands::proxy::*;

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let backend = BackendProcess::new();
            app.manage(Mutex::new(backend));

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            start_backend,
            stop_backend,
            get_backend_status,
            proxy_request,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
