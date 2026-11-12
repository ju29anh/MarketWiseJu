import type { AnalysisPayload } from '../types';

// Saved reports already contain these WDI codes, even before data_context existed.
const referenceLabels: Record<string, string> = {
  'TX.VAL.TECH.CD': 'Giá trị xuất khẩu công nghệ cao của Việt Nam',
  'SE.TER.ENRR': 'Tỷ lệ nhập học giáo dục đại học tại Việt Nam',
  'ST.INT.ARVL': 'Lượt khách quốc tế đến Việt Nam',
  'SH.XPD.CHEX.PC.CD': 'Chi y tế bình quân đầu người tại Việt Nam',
  'IT.NET.USER.ZS': 'Tỷ lệ người sử dụng Internet tại Việt Nam',
  'FS.AST.PRVT.GD.ZS': 'Tín dụng khu vực tư nhân tại Việt Nam',
  'IS.SHP.GOOD.TU': 'Lưu lượng container cảng biển Việt Nam',
  'SP.URB.TOTL.IN.ZS': 'Tỷ lệ dân số đô thị tại Việt Nam',
  'NE.CON.PRVT.PC.KD': 'Tiêu dùng hộ gia đình bình quân đầu người tại Việt Nam',
  'NY.GDP.PCAP.KD': 'GDP bình quân đầu người tại Việt Nam',
};

const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value);
const distinct = (rows: Record<string, unknown>[], column: string) => [...new Set(rows.map(r => r[column]).filter(v => typeof v === 'string' && v.trim()).map(String))];

export function formatMeasure(value: number | null | undefined, unit: string | null = null): string {
  if (!finite(value)) return 'Chưa xác định';
  const magnitude = Math.abs(value);
  const [divisor, suffix] = magnitude >= 1e12 ? [1e12, 'nghìn tỷ'] : magnitude >= 1e9 ? [1e9, 'tỷ'] : magnitude >= 1e6 ? [1e6, 'triệu'] : magnitude >= 1e4 ? [1e3, 'nghìn'] : [1, ''];
  const number = (value / divisor).toLocaleString('vi-VN', { maximumFractionDigits: 2 });
  return [number, suffix, unit].filter(Boolean).join(' ');
}

function friendlyTarget(column: string): string {
  const name = column.toLowerCase().replace(/[\s-]+/g, '_');
  if (/enroll|admission/.test(name)) return 'Số người nhập học';
  if (/revenue|doanh_thu/.test(name)) return 'Doanh thu';
  if (/units?_sold|sales_units|quantity|so_luong/.test(name)) return 'Số lượng bán';
  if (/price|gia_ban/.test(name)) return 'Giá bán';
  if (/booking|reservation/.test(name)) return 'Số lượt đặt dịch vụ';
  if (/subscriber|active_user/.test(name)) return 'Số người dùng';
  if (/shipment|delivery/.test(name)) return 'Số đơn vận chuyển';
  if (/sales|demand/.test(name)) return 'Doanh số / nhu cầu ghi nhận';
  return name === 'value' ? 'Chỉ tiêu định lượng trong tệp' : column.replace(/_/g, ' ');
}

function describeTime(periods: string[], count: number) {
  const first = periods[0], last = periods.at(-1);
  let cadence: 'year' | 'month' | 'day' | 'period' = 'period';
  let gaps = false;
  if (periods.length > 1 && periods.every(p => /^\d{4}$/.test(p))) {
    gaps = periods.some((p, i) => i > 0 && Number(p) - Number(periods[i - 1]) !== 1);
    if (!gaps) cadence = 'year';
  } else if (periods.length > 1 && periods.every(p => /^\d{4}-(0[1-9]|1[0-2])$/.test(p))) {
    const months = periods.map(p => Number(p.slice(0, 4)) * 12 + Number(p.slice(5)) - 1);
    gaps = months.some((p, i) => i > 0 && p - months[i - 1] !== 1);
    if (!gaps) cadence = 'month';
  } else if (periods.length > 1 && periods.every(p => /^\d{4}-\d{2}-\d{2}$/.test(p))) {
    const days = periods.map(p => Date.parse(p));
    if (days.every(Number.isFinite) && days.every((p, i) => i === 0 || p - days[i - 1] === 86400000)) cadence = 'day';
  }
  const labels = Array.from({ length: count }, (_, i) => {
    if (cadence === 'year') return String(Number(last) + i + 1);
    if (cadence === 'month' && last) {
      const month = Number(last.slice(0, 4)) * 12 + Number(last.slice(5)) + i;
      return `${Math.floor(month / 12)}-${String(month % 12 + 1).padStart(2, '0')}`;
    }
    if (cadence === 'day' && last) return new Date(Date.parse(last) + (i + 1) * 86400000).toISOString().slice(0, 10);
    return `Bước ${i + 1}`;
  });
  return { first, last, cadence, gaps, labels, range: first && last ? first === last ? first : `${first}–${last}` : 'Chưa rõ kỳ đo' };
}

function inputGuide(category: string, subject: string) {
  if (/Smartphones|Technology|Audio|Smart Home|Electric Vehicles/.test(category) || /whoop|watch|wearable|garmin|fitbit|vòng tay|đồng hồ/i.test(subject)) return {
    metric: 'số lượng bán và giá thực bán',
    fields: ['product_name', 'period', 'units_sold', 'unit_price_vnd'],
    instructions: 'Mỗi dòng là một tuần hoặc tháng của cùng mẫu và phiên bản; ghi số máy/thiết bị bán ra và giá thực bán bằng VND.',
    verification: 'Tên và phiên bản chính xác, thị trường bán, ngày công bố và đường dẫn nhà sản xuất hoặc nhà phân phối.',
  };
  if (/Education/.test(category)) return {
    metric: 'số hồ sơ, số người nhập học và học phí',
    fields: ['product_name', 'period', 'applications', 'enrollments', 'tuition_vnd'],
    instructions: 'Mỗi dòng là một kỳ tuyển sinh của cùng trường/ngành; tách số hồ sơ, số nhập học và học phí thực đóng bằng VND.',
    verification: 'Đề án tuyển sinh, biểu học phí và báo cáo công khai đúng trường/ngành, kèm năm áp dụng.',
  };
  if (/Food|FMCG|Fashion|Beauty/.test(category)) return {
    metric: 'số lượng bán, giá bán và chi phí đơn vị',
    fields: ['product_name', 'period', 'units_sold', 'unit_price_vnd', 'unit_cost_vnd'],
    instructions: 'Mỗi dòng là một tuần hoặc tháng của cùng sản phẩm/quy cách; ghi số lượng bán, giá thực thu và giá vốn trên một đơn vị.',
    verification: 'Đúng thương hiệu, quy cách sản phẩm, kênh bán và bảng giá áp dụng tại cùng thời điểm.',
  };
  if (/Tourism/.test(category)) return {
    metric: 'lượt đặt dịch vụ và giá trị giao dịch',
    fields: ['product_name', 'period', 'bookings', 'revenue_vnd'],
    instructions: 'Mỗi dòng là một tháng của cùng tour/cơ sở; ghi lượt đặt thành công và doanh thu thực thu, giữ rõ mùa vụ.',
    verification: 'Đúng tour/cơ sở, loại dịch vụ, địa bàn và điều kiện giá tại thời điểm đối chiếu.',
  };
  if (/Real Estate/.test(category)) return {
    metric: 'giao dịch thành công, giá giao dịch và lượng tin đăng',
    fields: ['product_name', 'period', 'transactions', 'avg_price_vnd', 'listing_count'],
    instructions: 'Mỗi dòng là một tháng của cùng dự án/loại nhà; ghi giao dịch thành công và giá theo cùng loại tài sản, diện tích, địa bàn.',
    verification: 'Đúng dự án, loại tài sản, diện tích và tình trạng pháp lý; đối chiếu giá giao dịch, tách giá rao bán.',
  };
  if (/FinTech|Digital Services/.test(category)) return {
    metric: 'người dùng hoạt động, giao dịch và doanh thu dịch vụ',
    fields: ['product_name', 'period', 'active_users', 'transactions', 'revenue_vnd'],
    instructions: 'Mỗi dòng là một tháng của cùng dịch vụ/gói; tách người dùng hoạt động, giao dịch hoàn tất và doanh thu thực thu.',
    verification: 'Đúng tổ chức/dịch vụ, gói sử dụng, biểu phí và kỳ báo cáo; tách tài khoản đăng ký khỏi người dùng hoạt động.',
  };
  if (/Logistics/.test(category)) return {
    metric: 'đơn giao hoàn tất, chi phí và tỷ lệ đúng hẹn',
    fields: ['product_name', 'period', 'shipments', 'cost_vnd', 'on_time_rate'],
    instructions: 'Mỗi dòng là một tuần/tháng của cùng tuyến hoặc dịch vụ; ghi đơn hoàn tất, tổng chi phí và tỷ lệ đúng hẹn với cùng cách tính.',
    verification: 'Đúng đơn vị vận chuyển, tuyến, loại hàng và cam kết thời gian; đối chiếu cùng địa bàn và kỳ đo.',
  };
  if (/Healthcare/.test(category)) return {
    metric: 'lượt sử dụng dịch vụ và doanh thu theo kỳ',
    fields: ['product_name', 'period', 'service_visits', 'revenue_vnd', 'cost_vnd'],
    instructions: 'Mỗi dòng là một tháng của cùng cơ sở/dịch vụ; dùng số lượt phục vụ tổng hợp, doanh thu và chi phí theo cùng phạm vi.',
    verification: 'Đúng cơ sở, dịch vụ, phạm vi chuyên môn và bảng phí công bố; không suy chất lượng chuyên môn từ số lượt sử dụng.',
  };
  return {
    metric: 'chỉ tiêu hoạt động theo thời gian',
    fields: ['product_name', 'period', 'observed_value', 'cost_vnd'],
    instructions: 'Mỗi dòng là một kỳ của đúng đối tượng; điền chỉ tiêu cần dự báo và chi phí liên quan, ghi rõ đơn vị và giữ các kỳ đều nhau.',
    verification: 'Tên chính xác, phạm vi hoạt động, định nghĩa chỉ tiêu và đường dẫn tài liệu công bố của đối tượng.',
  };
}

export function buildAnalysisReadout(data: AnalysisPayload) {
  const r = data.regression;
  const sample = data.data_validation.sample_data || [];
  const context = data.data_context;
  const codes = distinct(sample, 'indicator_code');
  const units = distinct(sample, 'unit');
  const code = context?.indicator_code || (codes.length === 1 ? codes[0] : null);
  let unitStatus = context?.unit_status || (units.length > 1 ? 'mixed' : units.length === 1 ? 'known' : 'unknown');
  const unit = unitStatus === 'mixed' ? null : context ? context.unit : units.length === 1 ? units[0] : /(?:^|_)usd$/i.test(r.target_variable) ? 'USD' : /(?:^|_)vnd$/i.test(r.target_variable) ? 'VND' : null;
  if(unitStatus==='unknown'&&unit)unitStatus='known';
  const metric = context?.indicator_label || (code && referenceLabels[code]) || friendlyTarget(r.target_variable);
  const legacy = Boolean(data.supporting_models_summary?.web_synthesis_meta);
  const national = data.evidence_scope?.analysis_mode === 'national_reference' || sample.some(s => s.scope === 'national_reference');
  const scope = national ? 'national' : data.evidence_scope?.matched_item === true ? 'entity' : 'dataset';
  const entities = context?.observed_entities || data.evidence_scope?.observed_entities || distinct(sample, 'observed_entity');
  const observedName = entities.join(', ') || (national ? 'Việt Nam' : scope === 'entity' ? data.product_name : 'Đối tượng trong tệp');
  const history = (r.chart_data || []).filter(p => finite(p.actual));
  const time = describeTime(history.map(p => p.period), r.future_forecast.length);
  const last = history.at(-1), previous = history.at(-2);
  const recentChange = previous && last && previous.actual !== 0 ? ((last.actual! - previous.actual!) / Math.abs(previous.actual!)) * 100 : null;
  const hasHoldout = r.validation ? r.validation.mode === 'heldout' : history.length >= 8;
  const r2 = finite(r.metrics.r2_score) ? r.metrics.r2_score : null;
  const quality = unitStatus==='mixed' || time.gaps ? 'weak' : !hasHoldout || r2 === null || !finite(r.metrics.mae) ? 'unvalidated' : r2 <= 0 || r.validation?.beats_baseline === false ? 'weak' : r.validation?.beats_baseline === true && r2 >= .5 && unit ? 'supported' : 'limited';
  const qualityLabel = quality === 'weak' ? 'Chưa dùng để chốt kế hoạch' : quality === 'unvalidated' ? 'Chưa có kiểm định độc lập' : quality === 'supported' ? 'Có thể thử nghiệm có kiểm soát' : 'Cần kiểm chứng thêm';
  const error = formatMeasure(r.metrics.mae, unit);
  const qualityReason = unitStatus==='mixed' ? 'Các dòng trong tệp đang dùng nhiều đơn vị khác nhau. Cần quy đổi về cùng đơn vị trước khi đọc mức thay đổi hoặc dùng dự báo.'
    : time.gaps ? 'Chuỗi có kỳ thiếu hoặc trùng. Cần chuẩn hóa mốc thời gian trước khi coi mỗi bước dự báo là một kỳ thực tế.'
    : !hasHoldout ? `Chuỗi chỉ có ${history.length} quan sát. Báo cáo chưa tách được phần dữ liệu riêng để kiểm tra dự báo.`
    : r2 === null ? 'Báo cáo chưa có kết quả kiểm định đủ để đánh giá khả năng dự báo.'
    : quality === 'weak' ? `Khi kiểm tra trên dữ liệu cũ, dự báo lệch trung bình khoảng ${error}${unit ? '' : ' (tệp chưa ghi rõ đơn vị)'}. ${r.validation?.beats_baseline === false ? 'Chưa tốt hơn cách lấy giá trị kỳ trước làm dự báo.' : 'Mô hình chưa giải thích tốt các biến động trong phần dữ liệu kiểm tra.'}`
    : `Sai lệch trung bình khi kiểm tra là ${error}${unit ? '' : ' (chưa rõ đơn vị)'}. ${quality === 'supported' ? 'Mô hình tốt hơn cách giữ giá trị kỳ trước trong lần kiểm tra này; vẫn cần theo dõi kỳ mới.' : 'Cần kiểm tra thêm bằng số liệu kỳ mới và cách dự báo đơn giản trước khi áp dụng.'}`;
  const guide = inputGuide(data.category,data.product_name);
  const recentReading = finite(recentChange)
    ? `Trong dữ liệu, chỉ tiêu kỳ gần nhất ${recentChange===0?'giữ nguyên':`${recentChange>0?'tăng':'giảm'} ${Math.abs(recentChange).toLocaleString('vi-VN',{maximumFractionDigits:2})}%`} so với kỳ trước`
    : `Giá trị gần nhất trong dữ liệu: ${formatMeasure(last?.actual,unit)}`;
  const title = legacy ? 'Báo cáo này cần được phân tích lại' : scope !== 'entity' ? `Chưa thể kết luận riêng về ${data.product_name}` : quality === 'weak' || quality === 'unvalidated' ? `Dự báo cho ${data.product_name} chưa đủ cơ sở để sử dụng` : recentReading;
  const summary = legacy ? 'Báo cáo cũ có dữ liệu tổng hợp chưa được kiểm chứng. Hãy nạp dữ liệu có nguồn để tạo kết quả mới.'
    : national ? `Dữ liệu dùng trong lần chạy này là “${metric}”${unit ? ` (${unit})` : ''}, gồm ${history.length} quan sát giai đoạn ${time.range}. Chuỗi này mô tả ${observedName}, chưa đo ${guide.metric} riêng của ${data.product_name}.`
    : scope === 'dataset' ? `Đã tính toán trên ${history.length} quan sát của tệp, nhưng chưa xác nhận các dòng dữ liệu thuộc đúng ${data.product_name}. Cần kiểm tra cột tên đối tượng trước khi diễn giải kết quả.`
    : `Đang đo “${metric}” từ ${history.length} quan sát của ${data.product_name}, giai đoạn ${time.range}. ${unit ? `Đơn vị: ${unit}.` : 'Tệp chưa ghi rõ đơn vị; cần bổ sung trước khi dùng các con số để ra quyết định.'}`;

  const actions = scope !== 'entity' ? [
    { title: `Xác minh thông tin về ${data.product_name}`, description: guide.verification, deliverable: 'Một hồ sơ đúng đối tượng, có nguồn và ngày kiểm tra.' },
    { title: `Bổ sung ${guide.metric}`, description: guide.instructions + ' Nên có ít nhất 8 kỳ để dành một phần dữ liệu kiểm tra.', deliverable: 'Một tệp CSV/XLSX của đúng đối tượng, mỗi dòng một kỳ, có nguồn để đối chiếu.' },
    { title: 'Phân tích lại trên dữ liệu vừa bổ sung', description: 'Kiểm tra tên đối tượng, đơn vị và kỳ đo trước khi chạy. Chỉ dùng dự báo khi sai số đáp ứng mức chấp nhận của kế hoạch thực tế.', deliverable: 'Báo cáo có dữ liệu riêng của đối tượng và kết quả kiểm tra trên phần dữ liệu chưa dùng huấn luyện.' },
  ] : [
    { title: time.gaps ? 'Bổ sung các kỳ đang thiếu' : `Kiểm tra số liệu sau ${time.last || 'kỳ gần nhất'}`, description: time.gaps ? 'Chuỗi hiện có kỳ bị thiếu hoặc trùng. Đối chiếu lại mốc thời gian; chưa gắn các bước dự báo thành ngày/tháng/năm cụ thể.' : `Đối chiếu “${metric}” ở kỳ mới với tệp gốc; giữ cùng cách đo${unit ? ` và đơn vị ${unit}` : ''}.`, deliverable: 'Một bảng cập nhật có ngày đo, giá trị thực tế và nguồn cho từng dòng.' },
    { title: quality === 'supported' ? 'Thử ở phạm vi nhỏ' : 'Kiểm tra sai số trước khi chốt kế hoạch', description: quality === 'supported' ? 'Chọn một kênh/nhóm khách hàng, đặt ngân sách và điều kiện dừng trước khi thử. Theo dõi giá trị thực tế so với dự báo sau mỗi kỳ.' : 'Dành các kỳ mới để kiểm tra; so sánh với cách giữ nguyên giá trị kỳ trước. Chưa tăng hàng nhập hoặc ngân sách chỉ từ mức tăng dự báo.', deliverable: 'Bảng giá trị thực tế, dự báo và chênh lệch theo từng kỳ; ngưỡng sai số chấp nhận được.' },
    { title: `Ra quyết định theo ${guide.metric}`, description: 'Đối chiếu tín hiệu nhu cầu với chi phí, giá bán và khả năng đáp ứng. Chỉ điều chỉnh quy mô khi dữ liệu kỳ mới xác nhận kết quả thử nghiệm.', deliverable: 'Một quyết định có người phụ trách, chi phí dự kiến và ngày đánh giá lại.' },
  ];
  const sourceUrls = [...new Set(context?.source_urls || distinct(sample, 'source_url'))].filter(url => {
    try { const parsed = new URL(url); return parsed.protocol === 'https:' && !parsed.username && !parsed.password; } catch { return false; }
  });
  const subjectSources = (data.web_research?.sources || [])
    .filter(source => source.match_status === 'exact' || source.identity_match === true)
    .filter(source => { try { return new URL(source.url).protocol==='https:'; } catch { return false; } })
    .sort((a,b) => Number(/[à-ỹđ]/i.test(b.excerpt)) - Number(/[à-ỹđ]/i.test(a.excerpt)))
    .slice(0,3);
  const facts = legacy ? [] : [
    { label: 'Chỉ tiêu thực sự được phân tích', value: metric, note: `${observedName}${unit ? ` · ${unit}` : ' · Chưa xác định đơn vị'}` },
    { label: `Giá trị gần nhất · ${last?.period || 'chưa rõ kỳ'}`, value: formatMeasure(last?.actual, unit), note: previous ? `Kỳ ${previous.period}: ${formatMeasure(previous.actual, unit)}${finite(recentChange) ? ` · ${recentChange > 0 ? '+' : ''}${recentChange.toLocaleString('vi-VN', { maximumFractionDigits: 2 })}% giữa hai quan sát` : ''}.` : 'Chưa có quan sát trước đó để đối chiếu.' },
    { label: 'Khả năng dùng dự báo', value: qualityLabel, note: qualityReason },
  ];
  return { scope, national, legacy, metric, unit, unitStatus, code, observedName, history, time, last, recentChange, quality, qualityLabel, qualityReason, title, summary, actions, guide, sourceUrls, subjectSources, facts };
}

export function analysisSummaryMarkdown(data: AnalysisPayload, report = buildAnalysisReadout(data)): string {
  return [`# Kết quả cho ${data.product_name}`, `## Kết luận\n${report.title}\n\n${report.summary}`,
    ...report.facts.map(f => `### ${f.label}\n${f.value}\n\n${f.note}`),
    '## Việc nên làm tiếp theo', ...report.actions.map((a, i) => `### ${i + 1}. ${a.title}\n${a.description}\n\nKết quả cần có: ${a.deliverable}`),
    ...(report.subjectSources.length?['## Tài liệu về đúng từ khóa (tách khỏi dữ liệu dự báo)',...report.subjectSources.map(s=>`### ${s.title}\n${s.excerpt}\n\nNguồn cần đối chiếu: ${s.url}`)]:[]),
    '## Cột trong tệp mẫu', report.guide.fields.join(', '),
    '## Nguồn và phạm vi', `Bộ dữ liệu: ${data.dataset_name}. Mã báo cáo: ${data.session_id}.`,
    ...report.sourceUrls.map(url => `- ${url}`), `Phạm vi: ${report.observedName}. Chỉ tiêu: ${report.metric}. Kỳ: ${report.time.range}.`,
    ...(!report.legacy ? ['## Dự báo để đối chiếu', `Mức sử dụng: ${report.qualityLabel}. ${report.qualityReason}`, `Dự báo tính từ mốc ${report.time.last || 'cuối chuỗi'}, chưa phải số liệu đã xảy ra.`,
      ...data.regression.future_forecast.map((p,i)=>`- ${report.time.labels[i]}: ${formatMeasure(p.forecast_value,report.unit)}; khoảng tham khảo ${formatMeasure(p.lower_bound,report.unit)}–${formatMeasure(p.upper_bound,report.unit)}.`)] : []),
  ].join('\n\n');
}
