use std::process::{Child, Command};
use std::sync::atomic::{AtomicBool, Ordering};

static BACKEND_RUNNING: AtomicBool = AtomicBool::new(false);

pub struct BackendProcess {
    process: Option<Child>,
    port: u16,
}

impl BackendProcess {
    pub fn new() -> Self {
        Self {
            process: None,
            port: 8000,
        }
    }

    pub fn start(&mut self) -> Result<(), String> {
        if BACKEND_RUNNING.load(Ordering::SeqCst) {
            return Ok(());
        }

        let python_path = Self::find_python();
        let backend_path = Self::find_backend_path();

        let child = Command::new(&python_path)
            .args(["-m", "uvicorn", "backend.main:app"])
            .args(["--host", "127.0.0.1"])
            .args(["--port", &self.port.to_string()])
            .current_dir(&backend_path)
            .spawn()
            .map_err(|e| format!("Failed to start backend: {}", e))?;

        self.process = Some(child);
        BACKEND_RUNNING.store(true, Ordering::SeqCst);

        Ok(())
    }

    pub fn stop(&mut self) -> Result<(), String> {
        if let Some(mut child) = self.process.take() {
            child.kill().map_err(|e| format!("Failed to stop backend: {}", e))?;
        }
        BACKEND_RUNNING.store(false, Ordering::SeqCst);
        Ok(())
    }

    pub fn is_running(&self) -> bool {
        BACKEND_RUNNING.load(Ordering::SeqCst)
    }

    pub fn port(&self) -> u16 {
        self.port
    }

    fn find_python() -> String {
        if cfg!(windows) {
            "python".to_string()
        } else {
            "python3".to_string()
        }
    }

    fn find_backend_path() -> std::path::PathBuf {
        std::env::current_dir()
            .unwrap_or_else(|_| std::path::PathBuf::from("."))
    }
}

impl Default for BackendProcess {
    fn default() -> Self {
        Self::new()
    }
}

impl Drop for BackendProcess {
    fn drop(&mut self) {
        let _ = self.stop();
    }
}
