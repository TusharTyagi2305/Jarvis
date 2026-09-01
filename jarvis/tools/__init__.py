from jarvis.tools.base import BaseTool, ToolResult
from jarvis.tools.registry import ToolRegistry
from jarvis.tools.system_tools import GetSystemInfoTool, TakeScreenshotTool, OpenApplicationTool, CloseApplicationTool
from jarvis.tools.file_tools import ReadFileTool, CreateFileTool, CreateFolderTool, SearchFilesTool, RenameMoveFileTool, DeleteFileTool
from jarvis.tools.terminal_tools import TerminalCommandTool
from jarvis.tools.browser_tools import (
    BrowserOpenTool,
    BrowserNavigateTool,
    BrowserSearchTool,
    BrowserGetPageInfoTool,
    BrowserGetTextTool,
    BrowserClickTool,
    BrowserTypeTool,
    BrowserPressKeyTool,
    BrowserScrollTool,
    BrowserBackTool,
    BrowserForwardTool,
    BrowserNewTabTool,
    BrowserSwitchTabTool,
    BrowserCloseTabTool,
    BrowserScreenshotTool,
    BrowserDownloadTool
)

from jarvis.tools.vision_tools import (
    ScreenCaptureTool,
    ScreenAnalyzeTool,
    ScreenFindElementTool,
    ScreenClickTool,
    ScreenTypeTool,
    ScreenPressKeyTool
)

from jarvis.tools.memory_tools import (
    MemorySaveTool,
    MemorySearchTool,
    MemoryGetTool,
    MemoryUpdateTool,
    MemoryDeleteTool,
    MemoryListTool,
    MemoryForgetTool
)

def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(GetSystemInfoTool())
    registry.register(TakeScreenshotTool())
    registry.register(OpenApplicationTool())
    registry.register(CloseApplicationTool())
    registry.register(ReadFileTool())
    registry.register(CreateFileTool())
    registry.register(CreateFolderTool())
    registry.register(SearchFilesTool())
    registry.register(RenameMoveFileTool())
    registry.register(DeleteFileTool())
    registry.register(TerminalCommandTool())
    # Browser Tools
    registry.register(BrowserOpenTool())
    registry.register(BrowserNavigateTool())
    registry.register(BrowserSearchTool())
    registry.register(BrowserGetPageInfoTool())
    registry.register(BrowserGetTextTool())
    registry.register(BrowserClickTool())
    registry.register(BrowserTypeTool())
    registry.register(BrowserPressKeyTool())
    registry.register(BrowserScrollTool())
    registry.register(BrowserBackTool())
    registry.register(BrowserForwardTool())
    registry.register(BrowserNewTabTool())
    registry.register(BrowserSwitchTabTool())
    registry.register(BrowserCloseTabTool())
    registry.register(BrowserScreenshotTool())
    registry.register(BrowserDownloadTool())
    # Vision Tools
    registry.register(ScreenCaptureTool())
    registry.register(ScreenAnalyzeTool())
    registry.register(ScreenFindElementTool())
    registry.register(ScreenClickTool())
    registry.register(ScreenTypeTool())
    registry.register(ScreenPressKeyTool())
    # Memory Tools
    registry.register(MemorySaveTool())
    registry.register(MemorySearchTool())
    registry.register(MemoryGetTool())
    registry.register(MemoryUpdateTool())
    registry.register(MemoryDeleteTool())
    registry.register(MemoryListTool())
    registry.register(MemoryForgetTool())
    return registry

__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolRegistry",
    "GetSystemInfoTool",
    "TakeScreenshotTool",
    "OpenApplicationTool",
    "CloseApplicationTool",
    "ReadFileTool",
    "CreateFileTool",
    "CreateFolderTool",
    "SearchFilesTool",
    "RenameMoveFileTool",
    "DeleteFileTool",
    "TerminalCommandTool",
    "BrowserOpenTool",
    "BrowserNavigateTool",
    "BrowserSearchTool",
    "BrowserGetPageInfoTool",
    "BrowserGetTextTool",
    "BrowserClickTool",
    "BrowserTypeTool",
    "BrowserPressKeyTool",
    "BrowserScrollTool",
    "BrowserBackTool",
    "BrowserForwardTool",
    "BrowserNewTabTool",
    "BrowserSwitchTabTool",
    "BrowserCloseTabTool",
    "BrowserScreenshotTool",
    "BrowserDownloadTool",
    "ScreenCaptureTool",
    "ScreenAnalyzeTool",
    "ScreenFindElementTool",
    "ScreenClickTool",
    "ScreenTypeTool",
    "ScreenPressKeyTool",
    "MemorySaveTool",
    "MemorySearchTool",
    "MemoryGetTool",
    "MemoryUpdateTool",
    "MemoryDeleteTool",
    "MemoryListTool",
    "MemoryForgetTool",
    "create_default_registry"
]
