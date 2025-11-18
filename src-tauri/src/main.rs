// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod file_ops;
mod git_ops;

use file_ops::*;
use git_ops::*;

// Only import process types when building for production
#[cfg(not(debug_assertions))]
use tauri::api::process::{Command, CommandEvent};

const BACKEND_HOST: &str = "127.0.0.1";
const BACKEND_PORT: u16 = 8000;

#[tauri::command]
fn check_backend_health() -> Result<bool, String> {
    // Simple health check - try to connect to the backend
    match std::net::TcpStream::connect(format!("{}:{}", BACKEND_HOST, BACKEND_PORT)) {
        Ok(_) => Ok(true),
        Err(_) => Ok(false),
    }
}

/// Wait for the backend to become healthy with exponential backoff
fn wait_for_backend_health(max_attempts: u32, initial_delay_ms: u64) -> bool {
    let mut delay = initial_delay_ms;

    for attempt in 1..=max_attempts {
        println!("Checking backend health (attempt {}/{})", attempt, max_attempts);

        match std::net::TcpStream::connect(format!("{}:{}", BACKEND_HOST, BACKEND_PORT)) {
            Ok(_) => {
                println!("Backend is healthy and ready!");
                return true;
            }
            Err(e) => {
                if attempt < max_attempts {
                    println!("Backend not ready yet ({}), retrying in {}ms...", e, delay);
                    std::thread::sleep(std::time::Duration::from_millis(delay));
                    // Exponential backoff with max of 5 seconds
                    delay = std::cmp::min(delay * 2, 5000);
                } else {
                    eprintln!("Backend failed to start after {} attempts", max_attempts);
                }
            }
        }
    }

    false
}

#[tauri::command]
async fn select_directory() -> Result<String, String> {
    use tauri::api::dialog::blocking::FileDialogBuilder;

    match FileDialogBuilder::new()
        .set_title("Select Project Location")
        .pick_folder()
    {
        Some(path) => Ok(path.to_string_lossy().to_string()),
        None => Err("No directory selected".to_string()),
    }
}

#[tauri::command]
fn get_home_dir() -> Result<String, String> {
    match dirs::home_dir() {
        Some(path) => Ok(path.to_string_lossy().to_string()),
        None => Err("Could not determine home directory".to_string()),
    }
}

fn start_backend_server(_app_handle: tauri::AppHandle) {
    std::thread::spawn(move || {
        // In production, use the sidecar binary
        #[cfg(not(debug_assertions))]
        {
            let port_arg = BACKEND_PORT.to_string();
            println!("Starting backend server on {}:{}", BACKEND_HOST, BACKEND_PORT);

            let (mut rx, _child) = Command::new_sidecar("novel-writer-backend")
                .expect("failed to create `novel-writer-backend` binary command")
                .args(&["--host", BACKEND_HOST, "--port", &port_arg])
                .spawn()
                .expect("Failed to spawn backend server");

            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => println!("Backend: {}", line),
                        CommandEvent::Stderr(line) => eprintln!("Backend Error: {}", line),
                        CommandEvent::Error(err) => eprintln!("Backend Process Error: {}", err),
                        CommandEvent::Terminated(payload) => {
                            eprintln!("Backend terminated with code: {:?}", payload.code);
                            break;
                        }
                        _ => {}
                    }
                }
            });
        }

        // In development, expect the backend to be run manually
        #[cfg(debug_assertions)]
        {
            println!("Development mode: Please start the Python backend manually:");
            println!("  cd python-backend && uvicorn main:app --reload --port {}", BACKEND_PORT);
        }
    });
}

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            // Start the backend server
            start_backend_server(app.handle());

            // Wait for the backend to become healthy with exponential backoff
            // Try up to 10 times, starting with 500ms delay
            // This allows for up to ~30 seconds total wait time
            #[cfg(not(debug_assertions))]
            {
                if !wait_for_backend_health(10, 500) {
                    eprintln!("Warning: Backend server may not be ready. The application will continue but some features may not work.");
                }
            }

            // In development, just wait a bit for manual backend startup
            #[cfg(debug_assertions)]
            {
                std::thread::sleep(std::time::Duration::from_millis(500));
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            read_file_content,
            write_file_content,
            list_directory,
            create_directory,
            delete_file,
            file_exists,
            init_git_repo,
            git_commit,
            git_status,
            git_log,
            git_diff,
            restore_file_version,
            check_backend_health,
            select_directory,
            get_home_dir
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
