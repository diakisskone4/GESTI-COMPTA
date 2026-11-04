export type Role = 'admin' | 'teacher' | 'student' | 'accountant';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  role_label: string;
  level: '' | 'BT1' | 'BT2';
  phone: string;
  establishment: string;
  is_active: boolean;
  date_joined: string;
  last_login: string | null;
}

export interface Lesson {
  id: number;
  title: string;
  objectives: string;
  content: string;
  definitions: string;
  formulas: string;
  example: string;
  status: 'draft' | 'published';
}

export interface Chapter {
  id: number;
  module: number;
  title: string;
  summary: string;
  formulas: string;
  calculator_slug: string;
  order: number;
  lessons: Lesson[];
  completed: boolean;
}

export interface Module {
  id: number;
  level: number;
  level_code: 'BT1' | 'BT2';
  code: string;
  title: string;
  objectives: string;
  description: string;
  order: number;
  official_check: boolean;
  chapters_count: number;
  completed_count: number;
  chapters?: Chapter[];
}

export interface Level {
  id: number;
  code: 'BT1' | 'BT2';
  title: string;
  description: string;
  modules: Module[];
}

export type FieldType = 'money' | 'number' | 'percent' | 'integer' | 'text' | 'select' | 'date' | 'table';

export interface FieldSpec {
  name: string;
  label: string;
  type: FieldType;
  required?: boolean;
  default?: unknown;
  help?: string;
  options?: { value: string; label: string }[];
  columns?: FieldSpec[];
  min?: string | number;
  max?: string | number;
  nullable?: boolean;
}

export interface CalculatorMeta {
  slug: string;
  title: string;
  level: 'BT1' | 'BT2';
  category: string;
  description: string;
  fields: FieldSpec[];
  reference: string;
}

export interface CalcOutput {
  formulas: string[];
  steps: { label: string; detail: string; value: string }[];
  results: { key: string; label: string; value: string; raw: string | null; highlight: boolean }[];
  tables: { title: string; columns: string[]; rows: string[][]; footer: string[] | null }[];
  entries: { group: string; account: string; label: string; debit: string; credit: string }[];
  interpretation: string[];
  warnings: string[];
}

export interface Company {
  id: number;
  name: string;
  legal_form: string;
  tax_id: string;
  rccm: string;
  address: string;
  city: string;
  currency: string;
  is_training: boolean;
  fiscal_years_count: number;
  entries_count: number;
}

export interface FiscalYear {
  id: number;
  company: number;
  label: string;
  start_date: string;
  end_date: string;
  is_closed: boolean;
}

export interface Journal {
  id: number;
  company: number;
  code: string;
  label: string;
  kind: string;
}

export interface Account {
  id: number;
  code: string;
  label: string;
  account_class: string;
  is_active: boolean;
  verified: boolean;
  is_custom: boolean;
}

export interface EntryLine {
  id?: number;
  account: number;
  account_code?: string;
  account_label?: string;
  label: string;
  debit: string;
  credit: string;
}

export interface JournalEntry {
  id: number;
  company: number;
  fiscal_year: number;
  journal: number;
  journal_code: string;
  number: number | null;
  date: string;
  reference: string;
  label: string;
  status: 'draft' | 'validated';
  status_label: string;
  reversal_of: number | null;
  reversed_by_id: number | null;
  lines: EntryLine[];
  total_debit: string;
  total_credit: string;
}

export interface Quiz {
  id: number;
  title: string;
  level: 'BT1' | 'BT2';
  module: number | null;
  module_title: string;
  kind: 'quiz' | 'evaluation' | 'mock';
  kind_label: string;
  description: string;
  duration_minutes: number;
  is_published: boolean;
  questions_count: number;
  best_grade: string | null;
  attempts_count: number;
}

export interface PublicQuestion {
  id: number;
  kind: 'mcq' | 'numeric' | 'entry';
  text: string;
  points: string;
  order: number;
  multiple: boolean;
  choices: { id: number; text: string }[];
}

export interface AttemptDetail {
  question: number;
  text: string;
  kind: string;
  answer: unknown;
  correct: boolean;
  points: string;
  max_points: string;
  expected: string;
  explanation: string;
}

export interface Attempt {
  id: number;
  quiz: number;
  quiz_title: string;
  quiz_level: string;
  quiz_kind: string;
  full_name: string;
  started_at: string;
  finished_at: string | null;
  score: string;
  max_score: string;
  grade: string | null;
  details: AttemptDetail[];
  timed_out: boolean;
}

export interface ExamSubject {
  id: number;
  title: string;
  level: 'BT1' | 'BT2';
  module: number | null;
  module_title: string;
  kind: 'annale' | 'mock' | 'devoir' | 'td';
  kind_label: string;
  session: string;
  duration_minutes: number | null;
  total_points: number;
  description: string;
  subject_name: string;
  correction_name: string;
  correction_text: string;
  correction_released: boolean;
  quiz: number | null;
  quiz_title: string;
  is_published: boolean;
  author: string;
  has_correction: boolean;
  has_correction_file: boolean;
  my_work: { opened_at: string | null; correction_viewed_at: string | null; self_grade: string | null; comment: string } | null;
  stats: { opened: number; corrected: number; graded: number; average: string | null } | null;
  created_at: string;
}

export interface SubjectResults {
  subject: string;
  summary: { students: number; opened: number; corrected: number; average: string | null; passed: number; graded: number };
  rows: { student: string; username: string; level: string; opened_at: string | null; correction_viewed_at: string | null;
    self_grade: string | null; comment: string; online_grade: string | null; online_attempts: number }[];
}
