import { createSlice } from "@reduxjs/toolkit";

interface SessionState {
  sessionId: string;
}

// Generate a random stable session ID for the current session lifecycle
const generateSessionId = () =>
  Math.random().toString(36).substring(2, 15) +
  Math.random().toString(36).substring(2, 15);

const initialState: SessionState = {
  sessionId: generateSessionId(),
};

const sessionSlice = createSlice({
  name: "session",
  initialState,
  reducers: {},
});

export default sessionSlice.reducer;
