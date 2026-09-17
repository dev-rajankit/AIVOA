import { configureStore } from "@reduxjs/toolkit";
import sessionReducer from "../features/session/sessionSlice";
import complaintFormReducer from "../features/complaint/complaintFormSlice";
import chatReducer from "../features/chat/chatSlice";
import riskAssessmentReducer from "../features/risk/riskAssessmentSlice";

export const store = configureStore({
  reducer: {
    session: sessionReducer,
    complaintForm: complaintFormReducer,
    chat: chatReducer,
    riskAssessment: riskAssessmentReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
