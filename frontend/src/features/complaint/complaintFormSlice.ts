import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { ComplaintFields } from "../../types/complaint";

export interface ComplaintFormState {
  currentForm: ComplaintFields;
  changedFields: string[];
  completenessPct: number;
  missingFields: string[];
}

const initialState: ComplaintFormState = {
  currentForm: {},
  changedFields: [],
  completenessPct: 0,
  missingFields: [],
};

const complaintFormSlice = createSlice({
  name: "complaintForm",
  initialState,
  reducers: {
    applyFormPatch(
      state,
      action: PayloadAction<{
        patch?: ComplaintFields;
        changedFields: string[];
        completenessPct: number;
        missingFields: string[];
      }>
    ) {
      const { patch, changedFields, completenessPct, missingFields } =
        action.payload;
        
      if (patch) {
        state.currentForm = {
          ...state.currentForm,
          ...patch,
        };
      }
      
      state.changedFields = changedFields;
      state.completenessPct = completenessPct;
      state.missingFields = missingFields;
    },
  },
});

export const { applyFormPatch } = complaintFormSlice.actions;
export default complaintFormSlice.reducer;
