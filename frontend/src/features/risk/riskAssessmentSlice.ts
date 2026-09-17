import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { RiskAssessment } from "../../types/complaint";

export interface RiskAssessmentState {
  currentRisk: RiskAssessment | null;
}

const initialState: RiskAssessmentState = {
  currentRisk: null,
};

const riskAssessmentSlice = createSlice({
  name: "riskAssessment",
  initialState,
  reducers: {
    applyRiskPatch(state, action: PayloadAction<RiskAssessment | null>) {
      if (action.payload) {
        const safePatch = Object.fromEntries(
          Object.entries(action.payload).filter(([_, v]) => v !== null && v !== undefined)
        );
        state.currentRisk = {
          ...state.currentRisk,
          ...safePatch,
        };
      }
    },
  },
});

export const { applyRiskPatch } = riskAssessmentSlice.actions;
export default riskAssessmentSlice.reducer;
