import type { SubjectReport, SubjectSource, SubjectClaim } from '../components/SubjectReportPanel';
import type { MarketReport } from '../components/MarketReportPanel';

export const sourceKind:Record<string,string> = {
  official:'Nhà sản xuất', institution:'Cơ quan / cơ sở đào tạo', publication:'Báo chí',
  reference:'Tài liệu tham khảo', headline:'Tiêu đề tin tức', web:'Website công khai'
};

export function referenceMarkdown(r:MarketReport):string[] {
  const p=r.provenance,q=r.quantitative;
  return ['## Bối cảnh định lượng cấp quốc gia', `Phạm vi: ${p.scope_label}. Đối tượng quan sát: ${p.observed_entity}.`,
    `Chỉ tiêu: ${p.indicator_label}. Đơn vị: ${p.unit}.`,
    `Chuỗi này chưa đo nhu cầu, giá bán hoặc doanh số riêng của ${r.query}.`,
    ...(p.source_url?[`Nguồn: [${p.source_name}](${p.source_url})`]:[]),
    ...r.training_data.map(row=>`- ${row.period}: ${row.value} ${p.unit}`),
    ...(q?[`Kiểm định: MAE ${q.validation.mae}; MAE cách đơn giản ${q.validation.baseline_mae}.`,q.validation.note]:[]),
    ...(r.data_issue?[r.data_issue]:[])];
}

export const sectionInfo = {
  overview: {title:'Thông tin cụ thể về đối tượng', empty:'Chưa có tài liệu khớp tên để mô tả đối tượng này.'},
  market: {title:'Thị trường & vị thế cạnh tranh', empty:'Tài liệu tìm được chưa đủ để kết luận về nhu cầu, doanh số hoặc vị thế cạnh tranh của đúng đối tượng.'},
  pricing: {title:'Giá, chi phí & phương án định giá', empty:'Chưa tìm thấy mức giá hoặc học phí đủ ngữ cảnh cho đúng đối tượng. Chưa đề xuất giá bán khi thiếu dữ liệu chi phí và nhu cầu.'},
  risks: {title:'Rủi ro & điểm cần lưu ý', empty:'Chưa có dẫn chứng đủ cụ thể để nêu rủi ro riêng của đối tượng; không gán sự cố hay bất lợi giả định thành sự thật.'},
};

export function subjectMarkdown(report:SubjectReport,sources:SubjectSource[]):string[] {
  const quote=(c:SubjectClaim)=>{
    const s=sources.find(s=>s.source_id===c.source_id);
    return [`### ${c.title}`,`Loại: ${c.kind==='inference'?'Nhận định / đề xuất':'Thông tin nguồn công bố'}${c.evidence_status==='unconfirmed'?' — chưa xác nhận / dự kiến':''}`,c.text,
      `> ${c.quote}`,s?`Nguồn ${c.source_id}: [${s.title}](${s.url})${s.published_at?' — '+s.published_at:''}`:'',...(c.measure?[`Theo dõi / bàn giao: ${c.measure}`]:[])];
  };
  return [`## ${report.query}`,report.identity.message,...(Object.keys(sectionInfo) as (keyof typeof sectionInfo)[]).flatMap(id=>[
    `## ${sectionInfo[id].title}`,...(report.sections[id].length?report.sections[id].flatMap(quote):[sectionInfo[id].empty])]),
    '## Hành động đề xuất',...report.actions.flatMap(quote),'## Chưa xác nhận',...report.missing.map(m=>'- '+m),
    `Mã hồ sơ dữ liệu: ${report.dataset_id}`,report.data_status.reason,
    ...(report.related_subjects.length?['Phiên bản tách riêng: '+report.related_subjects.join(', ')]:[])];
}
