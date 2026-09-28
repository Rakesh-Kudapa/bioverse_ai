import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "../app/page";

describe("BioVerse landing page", () => {
  it("introduces the product without enabling unsourced search", () => {
    render(<Home />);

    expect(
      screen.getByRole("heading", { name: /explore life,\s*visually/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("searchbox", { name: /search bioverse/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /search coming soon/i })).toBeDisabled();
    expect(screen.getByText(/not medical advice/i)).toBeInTheDocument();
  });
});
