from collections.abc import Iterator
from .notebook import Notebook
from .errors import NotebookNotFoundError


class Registry:
    """
    Notebook 注册中心。

    所有 Notebook 实例在启动时注册到此，后续通过名称查找。
    """

    def __init__(self):
        self._notebooks: dict[str, Notebook] = {}

    # ---- 注册 / 注销 ----

    def register(self, name: str, notebook: Notebook) -> None:
        notebook.name = name
        self._notebooks[name] = notebook

    def unregister(self, name: str) -> None:
        self._notebooks.pop(name, None)

    # ---- 查找 ----

    def notebook(self, name: str) -> Notebook:
        nb = self._notebooks.get(name)
        if nb is None:
            raise NotebookNotFoundError(name)
        return nb

    def list_names(self) -> Iterator[str]:
        return iter(self._notebooks.keys())

    # ---- 迭代 ----

    def __iter__(self):
        return iter(self._notebooks.values())

    def __len__(self) -> int:
        return len(self._notebooks)

    def __contains__(self, name: str) -> bool:
        return name in self._notebooks

    def __repr__(self) -> str:
        names = ", ".join(self._notebooks.keys()) or "(空)"
        return f"<Registry: {names}>"
