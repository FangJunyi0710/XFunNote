"""FSM for notebook CRUD pages using the transitions library."""

import streamlit as st
from transitions import Machine


class NotebookFSM:
    """Finite State Machine for notebook pages.

    States: idle -> browsing <-> adding/editing
    """

    def __init__(self):
        self.machine = Machine(
            model=self,
            states=["idle", "browsing", "adding", "editing"],
            initial="idle",
            auto_transitions=False,
            queued=False,
        )

        # Query
        self.machine.add_transition("do_query", "idle", "browsing")
        # Browse actions
        self.machine.add_transition("start_add", "browsing", "adding")
        self.machine.add_transition("start_edit", "browsing", "editing")
        # Save result -> browse
        self.machine.add_transition("save_add", "adding", "browsing")
        self.machine.add_transition("save_edit", "editing", "browsing")
        self.machine.add_transition("delete_entry", "editing", "browsing")
        # Cancel (from both adding and editing)
        self.machine.add_transition("cancel", ["adding", "editing"], "browsing")


def get_store(notebook_name: str) -> dict:
    """Get or create the centralized state store for a notebook page."""
    key = f"nb_fsm_{notebook_name}"
    if key not in st.session_state:
        st.session_state[key] = {
            "fsm": NotebookFSM(),
            "limit": 20,
            "offset": 0,
            "n_filters": 1,
            "results": None,
            "sel_row": None,
            "sel_idx": None,
        }
    return st.session_state[key]
