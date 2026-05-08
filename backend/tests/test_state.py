from app.core.state import GlobalState


def test_global_state_update_and_get():
    state = GlobalState()
    session_id = "state_session"
    frame = b"frame"
    roi = (0.1, 0.1, 0.2, 0.2)

    state.update_frame(session_id, frame, roi)
    saved_frame, saved_roi = state.get_latest_frame(session_id)

    assert saved_frame == frame
    assert saved_roi == roi

    state.clean_session(session_id)
    saved_frame, saved_roi = state.get_latest_frame(session_id)
    assert saved_frame is None
    assert saved_roi is None
