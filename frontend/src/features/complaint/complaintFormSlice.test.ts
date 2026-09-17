import { describe, it, expect } from "vitest";
import complaintFormReducer, { applyFormPatch } from "./complaintFormSlice";

describe("complaintFormSlice", () => {
  it("should merge form patch and keep unrelated fields", () => {
    const initialState = {
      currentForm: {
        product_name: "Amoxicillin Capsules",
        batch_lot_number: "AMX24601",
        dosage_form: "FDF" as const,
      },
      changedFields: [],
      completenessPct: 50,
      missingFields: [],
      duplicateStatus: "UNIQUE" as const,
      duplicateMatches: [],
      complaintId: null,
    };

    const action = applyFormPatch({
      patch: { batch_lot_number: "AMX24602" },
      changedFields: ["batch_lot_number"],
      completenessPct: 60,
      missingFields: ["complaint_date"],
    });

    const nextState = complaintFormReducer(initialState, action);

    expect(nextState.currentForm.product_name).toBe("Amoxicillin Capsules");
    expect(nextState.currentForm.dosage_form).toBe("FDF");
    expect(nextState.currentForm.batch_lot_number).toBe("AMX24602");
    expect(nextState.changedFields).toEqual(["batch_lot_number"]);
    expect(nextState.completenessPct).toBe(60);
  });
});
