package xfun.notebooks

import xfun.core.Column
import xfun.core.Notebook

object AIMemoryNotebook : Notebook() {
    override val name = "aimemory"
    override val extraColumns = listOf(
        Column("title", "TEXT", index = true),
        Column("source", "TEXT"),
    )
}
