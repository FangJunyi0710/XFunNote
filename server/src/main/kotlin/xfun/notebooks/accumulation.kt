package xfun.notebooks

import xfun.core.Column
import xfun.core.Notebook

object AccumulationNotebook : Notebook() {
    override val name = "accumulation"
    override val extraColumns = listOf(
        Column("source", "TEXT", nullable = true),
    )
}
