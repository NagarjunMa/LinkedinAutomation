import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { tailoredResumesApi } from "@/app/lib/api/tailored-resumes";
import type { TailoredResumeDetail, TailoredResumeListItem } from "@/app/lib/api/types-v2";
import { TailoredResumeLibrary } from "../library";

const toastMock = vi.hoisted(() => vi.fn());

vi.mock("@/app/lib/api/tailored-resumes", () => ({
  tailoredResumesApi: {
    list: vi.fn(),
    get: vi.fn(),
    downloadPdf: vi.fn(),
  },
}));

vi.mock("@/components/ui/use-toast", () => ({
  useToast: () => ({ toast: toastMock }),
}));

const listItem: TailoredResumeListItem = {
  version_id: "ver-1",
  resume_document_id: "doc-1",
  source_filename: "base.pdf",
  company_name: "Coinbase",
  target_role_title: "Senior Software Engineer",
  role_category: "SWE",
  seniority: "senior",
  country_hint: "US",
  match_score: 91,
  template_id: "us-swe",
  accepted_change_count: 3,
  created_at: "2026-06-17T00:00:00Z",
  accepted_at: "2026-06-17T00:00:00Z",
};

const detail: TailoredResumeDetail = {
  ...listItem,
  resume_json: {
    contact: {
      name: "Nagarjun Mallesh",
      email: "nagarjun@example.com",
      phone: "+1-555-0100",
      links: [],
    },
    summary: "Backend engineer focused on distributed systems.",
    experience: [
      {
        company: "ML Technologies",
        role: "Systems Analyst / Software Engineer",
        dates: "Jul 2025 - Present",
        location: "Boston, MA",
        bullets: [
          {
            id: "b1",
            text: "Built RAG-based conversational AI systems using Python and AWS Bedrock.",
            raw_text: "Built RAG-based conversational AI systems using Python and AWS Bedrock.",
          },
        ],
      },
    ],
    education: [],
    skills: { hard: ["Python"], soft: [] },
    projects: [],
    certifications: [],
    raw_text: "Nagarjun Mallesh",
  },
  source_jd_text: "Build backend systems for crypto products.",
  extracted_requirements: { company_name: "Coinbase" },
  diff_plan: {},
  accepted_changes: [{ type: "bullet_update", bullet_id: "b1", new_text: "Built RAG systems." }],
};

describe("TailoredResumeLibrary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    toastMock.mockClear();
    vi.mocked(tailoredResumesApi.list).mockResolvedValue([listItem]);
    vi.mocked(tailoredResumesApi.get).mockResolvedValue(detail);
    vi.mocked(tailoredResumesApi.downloadPdf).mockResolvedValue(
      new Blob(["%PDF-test"], { type: "application/pdf" })
    );
    vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:resume");
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
  });

  it("lists, searches, and opens saved tailored resume details", async () => {
    render(<TailoredResumeLibrary />);

    expect(await screen.findByText("Coinbase")).toBeInTheDocument();
    expect(screen.getByText("Senior Software Engineer")).toBeInTheDocument();
    expect(screen.getByText("91")).toBeInTheDocument();
    expect(screen.getAllByText("3").length).toBeGreaterThan(0);

    fireEvent.change(screen.getByPlaceholderText(/search company/i), {
      target: { value: "coinbase" },
    });
    await waitFor(() => {
      expect(screen.getByText("Coinbase")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /review tailored resume/i }));

    expect(await screen.findByText("Nagarjun Mallesh")).toBeInTheDocument();
    expect(screen.getAllByText(/Backend engineer focused/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Build backend systems for crypto products/i)).toBeInTheDocument();
    expect(tailoredResumesApi.get).toHaveBeenCalledWith("ver-1");
  });

  it("downloads a PDF rendered from the saved resume JSON", async () => {
    render(<TailoredResumeLibrary />);

    await screen.findByText("Coinbase");
    fireEvent.click(screen.getByRole("button", { name: /download tailored resume/i }));

    await waitFor(() => {
      expect(tailoredResumesApi.downloadPdf).toHaveBeenCalledWith("ver-1", {
        template_id: "us-swe",
        filename: "coinbase-senior-software-engineer.pdf",
      });
    });
    expect(URL.createObjectURL).toHaveBeenCalled();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:resume");
  });
});
