import type { Assignment, Subject, User } from "@/types";

const h = (hours: number) => new Date(Date.now() + hours * 3600_000).toISOString();

export const user: User = {
  id: "u1", name: "Aarav Sen", email: "aarav@example.com",
  college: "Bhawanipur Global Campus", department: "Data Science", semester: 5, rollNumber: "DS-21-0427",
};

export const subjects: Subject[] = [
  { id: "dm", name: "Data Mining", code: "DS501", semester: 5, faculty: "Dr. R. Mukherjee" },
  { id: "ml", name: "Machine Learning", code: "DS502", semester: 5, faculty: "Prof. S. Banerjee" },
  { id: "st", name: "Statistics", code: "DS503", semester: 5, faculty: "Dr. A. Ghosh" },
  { id: "db", name: "Database Management Systems", code: "DS504", semester: 5, faculty: "Prof. P. Dutta" },
  { id: "bd", name: "Big Data Analytics", code: "DS505", semester: 5, faculty: "Dr. M. Roy" },
];

const base = { sourcePlatform: "Digiicampus (demo)", attachments: [] as string[] };
export const assignments: Assignment[] = [
  { ...base, id: "a1", title: "Clustering Algorithms", subjectId: "dm", faculty: "Dr. R. Mukherjee", totalMarks: 20, createdAt: h(-30), deadline: h(52), status: "awaiting_approval", priority: "high",
    description: "Explain K-Means, its trade-offs, and hierarchical clustering with an example.",
    questions: ["Explain K-Means clustering", "List its advantages and disadvantages", "Describe hierarchical clustering with an example"], attachments: ["clustering_brief.pdf"] },
  { ...base, id: "a2", title: "Bias–Variance Tradeoff Report", subjectId: "ml", faculty: "Prof. S. Banerjee", totalMarks: 15, createdAt: h(-10), deadline: h(30), status: "in_progress", priority: "high", description: "Short report with plots.", questions: ["Define bias and variance", "Show effect of model complexity"] },
  { ...base, id: "a3", title: "Hypothesis Testing Problems", subjectId: "st", faculty: "Dr. A. Ghosh", totalMarks: 10, createdAt: h(-5), deadline: h(120), status: "new", priority: "medium", description: "Solve five problems.", questions: ["Q1–Q5"] },
  { ...base, id: "a4", title: "Normalisation Case Study", subjectId: "db", faculty: "Prof. P. Dutta", totalMarks: 20, createdAt: h(-90), deadline: h(-6), status: "overdue", priority: "high", description: "Normalise to 3NF.", questions: ["Identify dependencies", "Normalise to 3NF"] },
  { ...base, id: "a5", title: "MapReduce Word Count", subjectId: "bd", faculty: "Dr. M. Roy", totalMarks: 25, createdAt: h(-200), deadline: h(-100), status: "submitted", priority: "low", description: "Implement and explain.", questions: ["Implement", "Explain"] },
  { ...base, id: "a6", title: "Decision Trees Worksheet", subjectId: "ml", faculty: "Prof. S. Banerjee", totalMarks: 10, createdAt: h(-20), deadline: h(200), status: "ai_generated", priority: "low", description: "Worksheet.", questions: ["Q1", "Q2"] },
  { ...base, id: "a7", title: "Association Rules Mini-Project", subjectId: "dm", faculty: "Dr. R. Mukherjee", totalMarks: 30, createdAt: h(-40), deadline: h(300), status: "pending", priority: "medium", description: "Apriori on a small dataset.", questions: ["Apply Apriori"] },
];

export const subjectName = (id: string) => subjects.find((s) => s.id === id)?.name ?? "Unknown";

export const weeklyCompletion = [
  { week: "W1", done: 2 }, { week: "W2", done: 3 }, { week: "W3", done: 1 },
  { week: "W4", done: 4 }, { week: "W5", done: 3 }, { week: "W6", done: 5 },
];

export const activity = [
  { id: 1, text: "New assignment detected: Clustering Algorithms", when: "2 h ago", tone: "signal" },
  { id: 2, text: "AI summary generated", when: "2 h ago", tone: "signal" },
  { id: 3, text: "Answer draft created (3 of 3 questions)", when: "1 h ago", tone: "signal" },
  { id: 4, text: "PDF generated — waiting for your review", when: "45 min ago", tone: "warn" },
];
