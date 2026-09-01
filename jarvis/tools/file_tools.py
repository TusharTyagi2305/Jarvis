import os
import shutil
import glob
from pathlib import Path
from typing import Dict, Any, List
from jarvis.tools.base import BaseTool, ToolResult, Tuple_Validation
from jarvis.security.permissions import RiskLevel

class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Reads text content from a specified file path."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "file_path": {
                "type": "STRING",
                "description": "Path to the file to read."
            },
            "max_bytes": {
                "type": "INTEGER",
                "description": "Maximum bytes to read (default 50000)."
            }
        },
        "required": ["file_path"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        path_str = kwargs.get("file_path")
        if not path_str or not isinstance(path_str, str):
            return Tuple_Validation(is_valid=False, error="file_path must be a non-empty string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        file_path = Path(kwargs["file_path"]).resolve()
        max_bytes = kwargs.get("max_bytes", 50000)

        if not file_path.exists():
            return ToolResult(
                success=False,
                error=f"File not found: '{file_path}'",
                recoverable=True
            )
        if not file_path.is_file():
            return ToolResult(
                success=False,
                error=f"Path is not a regular file: '{file_path}'",
                recoverable=True
            )

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(max_bytes)
            
            truncated = file_path.stat().st_size > max_bytes
            return ToolResult(
                success=True,
                data={
                    "path": str(file_path),
                    "size_bytes": file_path.stat().st_size,
                    "content": content,
                    "truncated": truncated
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Error reading file '{file_path}': {str(e)}", recoverable=True)


class CreateFileTool(BaseTool):
    name = "create_file"
    description = "Creates or overwrites a file with the specified content."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "file_path": {
                "type": "STRING",
                "description": "Path where the file should be created."
            },
            "content": {
                "type": "STRING",
                "description": "Content to write into the file."
            }
        },
        "required": ["file_path", "content"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        path_str = kwargs.get("file_path")
        if not path_str or not isinstance(path_str, str):
            return Tuple_Validation(is_valid=False, error="file_path must be a non-empty string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        file_path = Path(kwargs["file_path"]).resolve()
        content = kwargs.get("content", "")

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return ToolResult(
                success=True,
                data={
                    "path": str(file_path),
                    "size_bytes": len(content.encode("utf-8")),
                    "message": f"File '{file_path}' created successfully."
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to create file '{file_path}': {str(e)}", recoverable=True)


class CreateFolderTool(BaseTool):
    name = "create_folder"
    description = "Creates a directory path if it does not exist."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "folder_path": {
                "type": "STRING",
                "description": "Directory path to create."
            }
        },
        "required": ["folder_path"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        path_str = kwargs.get("folder_path")
        if not path_str or not isinstance(path_str, str):
            return Tuple_Validation(is_valid=False, error="folder_path must be a non-empty string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        folder_path = Path(kwargs["folder_path"]).resolve()

        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            return ToolResult(
                success=True,
                data={"path": str(folder_path), "message": f"Folder '{folder_path}' created/verified successfully."}
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to create folder '{folder_path}': {str(e)}", recoverable=True)


class SearchFilesTool(BaseTool):
    name = "search_files"
    description = "Searches for local files on disk matching a pattern inside a local directory path. DO NOT use for web, internet, YouTube, Google, or online search requests."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "directory": {
                "type": "STRING",
                "description": "Target directory to search."
            },
            "pattern": {
                "type": "STRING",
                "description": "Glob pattern (e.g. '*.pdf', '*.txt', '**/*.py')."
            },
            "limit": {
                "type": "INTEGER",
                "description": "Maximum number of results to return (default 50)."
            }
        },
        "required": ["directory", "pattern"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        directory = kwargs.get("directory")
        pattern = kwargs.get("pattern")
        if not directory or not isinstance(directory, str):
            return Tuple_Validation(is_valid=False, error="directory must be a non-empty string.")
        if not pattern or not isinstance(pattern, str):
            return Tuple_Validation(is_valid=False, error="pattern must be a non-empty string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        dir_path = Path(kwargs["directory"]).resolve()
        pattern = kwargs["pattern"]
        limit = kwargs.get("limit", 50)

        if not dir_path.exists() or not dir_path.is_dir():
            return ToolResult(success=False, error=f"Directory does not exist: '{dir_path}'", recoverable=True)

        try:
            matched_files = []
            if "**" in pattern:
                matches = dir_path.glob(pattern)
            else:
                matches = dir_path.glob(f"**/{pattern}") if not pattern.startswith("*") else dir_path.glob(pattern)

            for match in matches:
                if len(matched_files) >= limit:
                    break
                if match.is_file():
                    matched_files.append({
                        "name": match.name,
                        "path": str(match),
                        "size_bytes": match.stat().st_size
                    })

            return ToolResult(
                success=True,
                data={
                    "directory": str(dir_path),
                    "pattern": pattern,
                    "total_found": len(matched_files),
                    "files": matched_files
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to search files: {str(e)}", recoverable=True)


class RenameMoveFileTool(BaseTool):
    name = "rename_move_file"
    description = "Renames or moves a file or directory from source path to destination path."
    risk_level = RiskLevel.SAFE
    parameters = {
        "type": "OBJECT",
        "properties": {
            "source_path": {
                "type": "STRING",
                "description": "Existing file or folder path."
            },
            "destination_path": {
                "type": "STRING",
                "description": "Target destination path."
            }
        },
        "required": ["source_path", "destination_path"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        src = kwargs.get("source_path")
        dst = kwargs.get("destination_path")
        if not src or not isinstance(src, str):
            return Tuple_Validation(is_valid=False, error="source_path must be a non-empty string.")
        if not dst or not isinstance(dst, str):
            return Tuple_Validation(is_valid=False, error="destination_path must be a non-empty string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        source_path = Path(kwargs["source_path"]).resolve()
        dest_path = Path(kwargs["destination_path"]).resolve()

        if not source_path.exists():
            return ToolResult(success=False, error=f"Source path does not exist: '{source_path}'", recoverable=True)

        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(dest_path))
            return ToolResult(
                success=True,
                data={
                    "source": str(source_path),
                    "destination": str(dest_path),
                    "message": f"Successfully moved/renamed '{source_path.name}' to '{dest_path}'."
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to move/rename file: {str(e)}", recoverable=True)


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Deletes a specified file. Requires user confirmation."
    risk_level = RiskLevel.CONFIRM
    parameters = {
        "type": "OBJECT",
        "properties": {
            "file_path": {
                "type": "STRING",
                "description": "Path of file to delete."
            }
        },
        "required": ["file_path"]
    }

    def validate(self, **kwargs: Any) -> Tuple_Validation:
        path_str = kwargs.get("file_path")
        if not path_str or not isinstance(path_str, str):
            return Tuple_Validation(is_valid=False, error="file_path must be a non-empty string.")
        return Tuple_Validation(is_valid=True)

    def execute(self, **kwargs: Any) -> ToolResult:
        file_path = Path(kwargs["file_path"]).resolve()

        if not file_path.exists():
            return ToolResult(success=False, error=f"File to delete does not exist: '{file_path}'", recoverable=True)

        try:
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
            return ToolResult(
                success=True,
                data={"path": str(file_path), "message": f"File/folder '{file_path.name}' deleted successfully."}
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to delete '{file_path}': {str(e)}", recoverable=True)
