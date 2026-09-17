import { createSlice, createAsyncThunk, PayloadAction } from "@reduxjs/toolkit";
import { sendCopilotMessage } from "../../api/copilot";
import { applyFormPatch } from "../complaint/complaintFormSlice";
import { applyRiskPatch } from "../risk/riskAssessmentSlice";
import { RootState } from "../../app/store";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface ChatState {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
}

const initialState: ChatState = {
  messages: [
    {
      id: "initial",
      role: "assistant",
      content:
        "Tell me about the customer complaint, and I’ll help structure the complaint information.",
    },
  ],
  loading: false,
  error: null,
};

export const sendMessage = createAsyncThunk(
  "chat/sendMessage",
  async (messageContent: string, { dispatch, getState, rejectWithValue }) => {
    try {
      const state = getState() as RootState;
      const request: import("../../types/copilot").CopilotMessageRequest = {
        session_id: state.session.sessionId,
        message: messageContent,
        current_form: state.complaintForm.currentForm,
      };
      if (state.complaintForm.complaintId) {
        request.complaint_id = state.complaintForm.complaintId;
      }

      const response = await sendCopilotMessage(request);

      dispatch(
        applyFormPatch({
          patch: response.form_patch,
          changedFields: response.changed_fields,
          completenessPct: response.completeness_pct,
          missingFields: response.missing_fields,
          duplicateStatus: response.duplicate_status,
          duplicateMatches: response.duplicate_matches,
          complaintId: response.complaint_id,
        })
      );

      dispatch(applyRiskPatch(response.risk_patch || null));

      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || "Failed to send message");
    }
  }
);

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    addUserMessage(state, action: PayloadAction<string>) {
      state.messages.push({
        id: Date.now().toString(),
        role: "user",
        content: action.payload,
      });
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.loading = false;
        state.messages.push({
          id: Date.now().toString(),
          role: "assistant",
          content: action.payload.assistant_reply,
        });
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { addUserMessage } = chatSlice.actions;
export default chatSlice.reducer;
