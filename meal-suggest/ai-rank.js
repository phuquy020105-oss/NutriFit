// meal-suggest/ai-rank.js — AI (Gemini Flash) cho module gợi ý.
// rank(): CHỈ xếp hạng / chọn trong pool ĐÃ LỌC, không sáng tạo món mới.
// generateDishes(): sáng tạo mâm cơm MỚI cho thực đơn tổng (có validate
// trùng tên + chuẩn hóa cal_pct / mealType). Không gọi backend cũ.

const MS_AI_RANK = (() => {
  const MODELS = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash'];

  function fmtPrice(v) {
    return v ? `${Number(v).toLocaleString('vi-VN')}đ` : 'chưa rõ giá';
  }

  function buildPrompt(pool, mealMode, pantry, opts) {
    const isSingle = opts && opts.dishMode === 'single';
    const mealName = mealMode === 'lunch' ? 'BỮA TRƯA (ăn no, năng lượng bền bỉ)' : 'BỮA TỐI (thanh đạm, dễ tiêu, ngủ ngon)';
    const lines = pool.map((x, i) =>
      `${i}. "${x.opt.title}" | ${x.opt.calories}kcal | ${fmtPrice(x.opt.price)} | P:${x.opt.macros?.protein || 0}g C:${x.opt.macros?.carbs || 0}g F:${x.opt.macros?.fat || 0}g | có gì: ${x.opt.protein} | tinh bột: ${x.opt.carb} | nước chấm/nước dùng: ${x.opt.soup} | rau ăn kèm: ${x.opt.veggie}${x.opt.parts ? ` | thành phần: ${x.opt.parts}` : ''}${isSingle ? '' : ` | khớp ${x.score}/${pantry.length} nguyên liệu (${(x.matched || []).join(', ')})`}`
    ).join('\n');
    if (isSingle) {
      const budget = opts && opts.maxPrice > 0
        ? `Ngân sách tối đa: ${fmtPrice(opts.maxPrice)}/phần.`
        : 'Không giới hạn ngân sách.';
      return `Bạn là chuyên gia dinh dưỡng ẩm thực Việt Nam cho ứng dụng NutriFit.
Nhiệm vụ: XẾP HẠNG TOÀN BỘ ${pool.length} MÓN MUA NGOÀI QUÁN dưới đây cho ${mealName} — món ngon/phù hợp nhất xếp đầu.

${budget}

DANH SÁCH ỨNG VIÊN (đánh số từ 0):
${lines}

YÊU CẦU:
- CHỈ được xếp hạng các món trong danh sách trên, TUYỆT ĐỐI không sáng tạo món mới.
- Món mua ngoài nên không xét nguyên liệu sẵn có — ưu tiên món hợp bữa (trưa no, tối nhẹ), vừa túi tiền, cân bằng đạm-rau-tinh bột, đa dạng ở các vị trí đầu.
- Trả về DUY NHẤT một chuỗi JSON hợp lệ, không markdown, không văn bản thừa, đúng cấu trúc:
{"picks": [thứ_tự_hạng_1, thứ_tự_hạng_2, ...], "reasons": ["lý do ngắn cho hạng 1", "lý do cho hạng 2", ...]}
- "picks" phải gồm TẤT CẢ ${pool.length} số thứ tự (mỗi số từ 0 đến ${pool.length - 1}, không trùng lặp).
- "reasons" cùng độ dài với "picks", mỗi lý do dưới 15 từ.`;
    }
    return `Bạn là chuyên gia dinh dưỡng ẩm thực Việt Nam cho ứng dụng NutriFit.
Nhiệm vụ: XẾP HẠNG TOÀN BỘ ${pool.length} ứng viên dưới đây (đã lọc theo nguyên liệu sẵn có của người dùng) cho ${mealName} — món ngon/phù hợp nhất xếp đầu.

Nguyên liệu người dùng đang có: ${pantry.length ? pantry.join(', ') : '(không nhập — chọn món cân bằng dinh dưỡng)'}

DANH SÁCH ỨNG VIÊN (đánh số từ 0):
${lines}

YÊU CẦU:
- CHỈ được xếp hạng các món trong danh sách trên, TUYỆT ĐỐI không sáng tạo món mới.
- Ưu tiên món khớp nhiều nguyên liệu, cân bằng đạm-rau-tinh bột, đa dạng nguồn đạm ở các vị trí đầu.
- Trả về DUY NHẤT một chuỗi JSON hợp lệ, không markdown, không văn bản thừa, đúng cấu trúc:
{"picks": [thứ_tự_hạng_1, thứ_tự_hạng_2, ...], "reasons": ["lý do ngắn cho hạng 1", "lý do cho hạng 2", ...]}
- "picks" phải gồm TẤT CẢ ${pool.length} số thứ tự (mỗi số từ 0 đến ${pool.length - 1}, không trùng lặp).
- "reasons" cùng độ dài với "picks", mỗi lý do dưới 15 từ.`;
  }

  async function callGeminiJson(prompt, apiKey, maxTokens, temperature) {
    const temp = typeof temperature === 'number' ? temperature : 0.7;
    for (const model of MODELS) {
      try {
        const resp = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(apiKey)}`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              contents: [{ parts: [{ text: prompt }] }],
              generationConfig: { temperature: temp, topP: 0.9, maxOutputTokens: maxTokens || 4096, responseMimeType: 'application/json' }
            })
          }
        );
        if (!resp.ok) continue;
        const data = await resp.json();
        let text = data?.candidates?.[0]?.content?.parts?.[0]?.text || '';
        text = text.trim()
          .replace(/^```json/i, '').replace(/^```/, '')
          .replace(/```$/, '').trim();
        const parsed = JSON.parse(text);
        if (parsed) return parsed;
      } catch (e) { /* thử model kế tiếp */ }
    }
    return null;
  }

  function buildGeneratePrompt(count, mealFilter, existingTitles, pantry) {
    const mealDesc = mealFilter === 'lunch' ? 'BỮA TRƯA (ăn no, năng lượng bền bỉ)'
      : mealFilter === 'dinner' ? 'BỮA TỐI (thanh đạm, dễ tiêu, ngủ ngon)'
      : 'cả BỮA TRƯA lẫn BỮA TỐI (chia đều 2 bữa)';
    const avoid = existingTitles.length
      ? `KHÔNG trùng với các món đã có sau đây (kể cả biến thể gần giống):\n${existingTitles.slice(0, 80).join(' | ')}`
      : '';
    const pantryLine = pantry.length
      ? `Ưu tiên dùng các nguyên liệu người dùng đang có: ${pantry.join(', ')}.`
      : '';
    return `Bạn là chuyên gia dinh dưỡng ẩm thực Việt Nam cho ứng dụng NutriFit.
Nhiệm vụ: SÁNG TẠO ${count} MÂM CƠM gia đình Việt Nam mới lạ cho ${mealDesc}.

${avoid}
${pantryLine}

YÊU CẦU MỖI MÂM CƠM:
- Đủ 5 thành phần: món chính (cơm/bún/miến...), món mặn (thịt/cá/trứng/đậu...), món canh, món rau, tráng miệng (trái cây/sữa chua đơn giản).
- Tên món (title) ngắn gọn kiểu Việt Nam, ví dụ "Cơm gà xào sả ớt + canh bí đỏ".
- Bữa trưa: cal_pct từ 0.36 đến 0.42 (ăn no). Bữa tối: cal_pct từ 0.26 đến 0.30 (nhẹ nhàng).
- parts: liệt kê nguyên liệu chính cách nhau bằng dấu phẩy, để app chấm độ khớp.
- nutritionNotes: 1 câu lợi ích dưới 20 từ.

Trả về DUY NHẤT một chuỗi JSON hợp lệ, không markdown, đúng cấu trúc:
{"dishes": [{"title": "...", "carb": "...", "protein": "...", "soup": "...", "veggie": "...", "dessert": "...", "parts": "...", "cal_pct": 0.38, "mealType": "lunch", "nutritionNotes": "..."}]}
- "dishes" phải có đúng ${count} phần tử, mealType chỉ nhận "lunch" hoặc "dinner"${mealFilter === 'all' ? ' (chia đều 2 bữa)' : ` (toàn bộ là "${mealFilter}")`}.`;
  }

  function sanitizeDishes(raw, mealFilter, existingTitles) {
    const arr = raw && Array.isArray(raw.dishes) ? raw.dishes : null;
    if (!arr) return null;
    const seen = new Set(existingTitles.map((t) => String(t).toLowerCase().trim()));
    const out = [];
    for (const d of arr) {
      if (!d || typeof d.title !== 'string') continue;
      const title = d.title.trim();
      if (!title || seen.has(title.toLowerCase())) continue;
      let mealType = d.mealType === 'dinner' ? 'dinner' : 'lunch';
      if (mealFilter === 'lunch') mealType = 'lunch';
      if (mealFilter === 'dinner') mealType = 'dinner';
      let cal = Number(d.cal_pct);
      if (!Number.isFinite(cal)) cal = mealType === 'lunch' ? 0.38 : 0.28;
      cal = Math.min(0.42, Math.max(0.25, cal));
      const str = (v) => String(v ?? '').trim() || '—';
      out.push({
        ai: true, day: null,
        title,
        carb: str(d.carb), protein: str(d.protein), soup: str(d.soup),
        veggie: str(d.veggie), dessert: str(d.dessert),
        parts: str(d.parts), cal_pct: cal, mealType,
        nutritionNotes: str(d.nutritionNotes)
      });
      seen.add(title.toLowerCase());
    }
    return out;
  }

  // Sáng tạo món mới cho thực đơn tổng. Trả về mảng món đã validate, hoặc null khi lỗi.
  async function generateDishes(count, mealFilter, existingTitles, pantry, apiKey) {
    if (!apiKey) return null;
    try {
      const parsed = await callGeminiJson(buildGeneratePrompt(count, mealFilter, existingTitles || [], pantry || []),
        apiKey, 4096, 0.7);
      const dishes = sanitizeDishes(parsed, mealFilter, existingTitles || []);
      return dishes && dishes.length > 0 ? dishes : null;
    } catch (e) { return null; }
  }

  // Trả về { order: [vị trí trong pool], reasons: [], source: 'ai' | 'expert' }
  // order là thứ hạng TOÀN BỘ pool — nút "Đổi thực đơn khác" xoay vòng qua đó.
  async function rank(pool, mealMode, pantry, apiKey, opts) {
    if (!apiKey) return { order: pool.map((_, i) => i), reasons: [], source: 'expert' };
    try {
      const parsed = await callGeminiJson(buildPrompt(pool, mealMode, pantry, opts), apiKey, 2048, 0.3);
      if (parsed && Array.isArray(parsed.picks) && parsed.picks.length > 0) {
        const seen = new Set();
        const order = [];
        for (const raw of parsed.picks) {
          const i = Number(raw);
          if (Number.isInteger(i) && i >= 0 && i < pool.length && !seen.has(i)) {
            seen.add(i); order.push(i);
          }
        }
        // AI trả thiếu index -> bù bằng thứ hạng cục bộ, giữ AI xếp đầu.
        for (let i = 0; i < pool.length && order.length < pool.length; i++) {
          if (!seen.has(i)) { seen.add(i); order.push(i); }
        }
        if (order.length === pool.length) {
          const reasons = Array.isArray(parsed.reasons) ? parsed.reasons : [];
          return { order, reasons: order.map((_, k) => reasons[k] || ''), source: 'ai' };
        }
      }
    } catch (e) { /* rớt xuống fallback chuyên gia */ }
    return { order: pool.map((_, i) => i), reasons: [], source: 'expert' };
  }

  return { rank, generateDishes };
})();
