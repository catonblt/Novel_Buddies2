use git2::{Repository, Signature, IndexAddOption, DiffOptions, Oid};
use serde::{Deserialize, Serialize};
use std::path::Path;

#[derive(Serialize, Deserialize, Debug)]
pub struct CommitInfo {
    pub id: String,
    pub message: String,
    pub author: String,
    pub timestamp: i64,
}

#[tauri::command]
pub fn init_git_repo(path: String) -> Result<(), String> {
    Repository::init(&path).map_err(|e| format!("Failed to initialize git repository: {}", e))?;
    Ok(())
}

#[tauri::command]
pub fn git_commit(repo_path: String, message: String, author_name: String, author_email: String) -> Result<String, String> {
    let repo = Repository::open(&repo_path).map_err(|e| format!("Failed to open repository: {}", e))?;

    let signature = Signature::now(&author_name, &author_email)
        .map_err(|e| format!("Failed to create signature: {}", e))?;

    let mut index = repo.index().map_err(|e| format!("Failed to get index: {}", e))?;

    // Add all changes
    index.add_all(["*"].iter(), IndexAddOption::DEFAULT, None)
        .map_err(|e| format!("Failed to add files: {}", e))?;

    index.write().map_err(|e| format!("Failed to write index: {}", e))?;

    let tree_id = index.write_tree().map_err(|e| format!("Failed to write tree: {}", e))?;
    let tree = repo.find_tree(tree_id).map_err(|e| format!("Failed to find tree: {}", e))?;

    let parent_commit = match repo.head() {
        Ok(head) => Some(head.peel_to_commit().map_err(|e| format!("Failed to get parent commit: {}", e))?),
        Err(_) => None,
    };

    let parents = match &parent_commit {
        Some(commit) => vec![commit],
        None => vec![],
    };

    let commit_id = repo.commit(
        Some("HEAD"),
        &signature,
        &signature,
        &message,
        &tree,
        &parents,
    ).map_err(|e| format!("Failed to create commit: {}", e))?;

    Ok(commit_id.to_string())
}

#[tauri::command]
pub fn git_status(repo_path: String) -> Result<Vec<String>, String> {
    let repo = Repository::open(&repo_path).map_err(|e| format!("Failed to open repository: {}", e))?;

    let statuses = repo.statuses(None).map_err(|e| format!("Failed to get status: {}", e))?;

    let mut changed_files = Vec::new();
    for entry in statuses.iter() {
        if let Some(path) = entry.path() {
            changed_files.push(path.to_string());
        }
    }

    Ok(changed_files)
}

#[tauri::command]
pub fn git_log(repo_path: String, max_count: usize) -> Result<Vec<CommitInfo>, String> {
    let repo = Repository::open(&repo_path).map_err(|e| format!("Failed to open repository: {}", e))?;

    let mut revwalk = repo.revwalk().map_err(|e| format!("Failed to create revwalk: {}", e))?;
    revwalk.push_head().map_err(|e| format!("Failed to push head: {}", e))?;

    let mut commits = Vec::new();
    for (i, oid) in revwalk.enumerate() {
        if i >= max_count {
            break;
        }

        let oid = oid.map_err(|e| format!("Failed to get oid: {}", e))?;
        let commit = repo.find_commit(oid).map_err(|e| format!("Failed to find commit: {}", e))?;

        commits.push(CommitInfo {
            id: commit.id().to_string(),
            message: commit.message().unwrap_or("").to_string(),
            author: commit.author().name().unwrap_or("").to_string(),
            timestamp: commit.time().seconds(),
        });
    }

    Ok(commits)
}

#[tauri::command]
pub fn git_diff(repo_path: String, file_path: Option<String>) -> Result<String, String> {
    let repo = Repository::open(&repo_path).map_err(|e| format!("Failed to open repository: {}", e))?;

    let head = repo.head().map_err(|e| format!("Failed to get HEAD: {}", e))?;
    let tree = head.peel_to_tree().map_err(|e| format!("Failed to get tree: {}", e))?;

    let mut opts = DiffOptions::new();
    if let Some(path) = file_path {
        opts.pathspec(path);
    }

    let diff = repo.diff_tree_to_workdir(Some(&tree), Some(&mut opts))
        .map_err(|e| format!("Failed to create diff: {}", e))?;

    let stats = diff.stats().map_err(|e| format!("Failed to get stats: {}", e))?;
    let diff_text = stats.to_buf(git2::DiffStatsFormat::FULL, 80)
        .map_err(|e| format!("Failed to format diff: {}", e))?;

    Ok(diff_text.as_str().unwrap_or("").to_string())
}

#[tauri::command]
pub fn restore_file_version(repo_path: String, file_path: String, commit_id: String) -> Result<(), String> {
    let repo = Repository::open(&repo_path).map_err(|e| format!("Failed to open repository: {}", e))?;

    let oid = Oid::from_str(&commit_id).map_err(|e| format!("Invalid commit ID: {}", e))?;
    let commit = repo.find_commit(oid).map_err(|e| format!("Failed to find commit: {}", e))?;
    let tree = commit.tree().map_err(|e| format!("Failed to get tree: {}", e))?;

    let entry = tree.get_path(Path::new(&file_path))
        .map_err(|e| format!("File not found in commit: {}", e))?;

    let blob = repo.find_blob(entry.id())
        .map_err(|e| format!("Failed to find blob: {}", e))?;

    let content = blob.content();
    let full_path = Path::new(&repo_path).join(&file_path);

    std::fs::write(full_path, content)
        .map_err(|e| format!("Failed to write file: {}", e))?;

    Ok(())
}
