export const ASSISTANT_NAME = 'MarketWiseJu';

export type AdvisorReply = {
  conversation_id: string; query: string; question: string; answer: string;
  assumptions: string[]; questions: string[];
  steps: {title:string;when:string;action:string;deliverable:string;decision_rule:string}[];
  evidence: {source_id:string;title:string;url:string;quote:string;published_at:string|null;content_status:string|null}[];
  assistant_name?: string; generated_at: string; source_count: number; context_created_at: string | null;
  notice: string; scope?: {analysis_mode?: string;scope_label?:string} | null;
};

export function advisorMarkdown(turns: AdvisorReply[]): string {
  return ['# Trao đổi sau phân tích', ...turns.flatMap(t => [
    `## Bạn: ${t.question}`, `${ASSISTANT_NAME} · ${t.generated_at}`,
    `Ngữ cảnh: ${t.context_created_at||'Chưa rõ thời điểm'} · ${t.source_count} tài liệu đúng tên. Câu trả lời chưa tra cứu web mới.`,
    ...(t.scope?.analysis_mode==='national_reference'?[`Phạm vi ML: ${t.scope.scope_label||'Chỉ tiêu tham khảo quốc gia'}, chưa mô tả doanh số/nhu cầu riêng của sản phẩm.`]:[]),
    '### Nhận định & đề xuất cần kiểm nghiệm', t.answer,
    ...(t.steps.length?['Mốc thời gian, khoản chi thử và ngưỡng tiếp tục / dừng là đề xuất, chưa phải chuẩn ngành hoặc kết quả đã kiểm chứng.']:[]),
    ...t.assumptions.map(a => `Giả định: ${a}`),
    ...t.steps.flatMap(s => [`### ${s.when} · ${s.title}`, s.action, `Cần có: ${s.deliverable}`, `Tiếp tục / dừng: ${s.decision_rule}`]),
    ...t.evidence.map(e => `Nguồn [${e.source_id} — ${e.title}](${e.url}): “${e.quote}” (trích nguồn, chưa xác minh độc lập)`),
    ...t.questions.map(q => `Cần bổ sung: ${q}`), t.notice,
  ])].join('\n\n');
}

