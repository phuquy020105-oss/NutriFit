// NutriFit Frontend
// Extracted from the existing UI logic; behavior preserved.

    function applyLoadedProfile(p) {
      const goals = { weight_loss: 'lose', giam_can: 'lose', weight_gain: 'gain', tang_can: 'gain' };
      Object.assign(userProfile, {
        gender: String(p.Gender).toLowerCase(), age: p.Age, height: p.HeightCm, weight: p.WeightKg,
        goal: goals[String(p.Goal).toLowerCase()] || String(p.Goal).toLowerCase(),
        activity: p.ActivityLevel, bmr: p.Bmr, tdee: p.Tdee, targetKcal: p.TargetKcal,
        carbs: p.TargetCarbs, protein: p.TargetProtein, fat: p.TargetFat,
        fiber: p.TargetFiber, waterTarget: p.TargetWaterMl, bmi: p.Bmi
      });
      document.getElementById('inp-height').value = userProfile.height;
      document.getElementById('inp-weight').value = userProfile.weight;
      document.getElementById('inp-age-range').value = userProfile.age;
      document.getElementById('age-val').innerText = userProfile.age + ' tuổi';
      document.querySelectorAll('input[name="goal"]').forEach(el => { el.checked = el.value === userProfile.goal; });
      document.querySelectorAll('input[name="act"]').forEach(el => { el.checked = Number(el.value) === userProfile.activity; });
      setGender(userProfile.gender);
      updateDashboardUI();
    }

    function reOpenOnboarding() {
      isEditingProfile = true;
      currentStep = 1;
      updateStepUI();
      if (document.getElementById('inp-height')) document.getElementById('inp-height').value = userProfile.height || 172;
      if (document.getElementById('inp-weight')) document.getElementById('inp-weight').value = userProfile.weight || 68;
      if (document.getElementById('inp-age-range')) document.getElementById('inp-age-range').value = userProfile.age || 24;
      if (document.getElementById('age-val')) document.getElementById('age-val').innerText = `${userProfile.age || 24} tuổi`;
      setGender(userProfile.gender || 'male');
      updateStep3Preview();
      switchScreen('screen-onboarding');
    }

    // Kiểm tra tính hợp lệ và ràng buộc logic của từng bước Onboarding
    function validateStep(step) {
      if (step === 1) {
        const goal = document.querySelector('input[name="goal"]:checked')?.value;
        if (!goal || !['lose', 'maintain', 'gain'].includes(goal)) {
          alert("Vui lòng chọn một mục tiêu thể hình!");
          return false;
        }
        return true;
      }

      if (step === 2) {
        if (!userProfile.gender || !['male', 'female'].includes(userProfile.gender)) {
          alert("Vui lòng chọn giới tính!");
          return false;
        }
        const age = parseInt(document.getElementById('inp-age-range')?.value) || parseInt(document.getElementById('age-val')?.innerText);
        if (!age || isNaN(age) || age < 12 || age > 95) {
          alert("Độ tuổi không hợp lý! Vui lòng chọn độ tuổi từ 12 đến 95 tuổi.");
          return false;
        }
        return true;
      }

      if (step === 3) {
        const heightInput = document.getElementById('inp-height');
        const weightInput = document.getElementById('inp-weight');
        const h = parseFloat(heightInput.value);
        const w = parseFloat(weightInput.value);
        const errBox = document.getElementById('step3-error-msg');
        const errText = document.getElementById('step3-error-text');

        const showError = (msg, inputEl) => {
          if (errBox && errText) {
            errText.innerText = msg;
            errBox.classList.remove('hidden');
          } else {
            alert(msg);
          }
          if (inputEl) {
            inputEl.focus();
            inputEl.parentElement?.classList.add('border-rose-500', 'bg-rose-50/50');
            setTimeout(() => inputEl.parentElement?.classList.remove('border-rose-500', 'bg-rose-50/50'), 2500);
          }
        };

        if (isNaN(h) || h === null || heightInput.value.trim() === '') {
          showError("Vui lòng nhập chiều cao của bạn!", heightInput);
          return false;
        }
        if (h < 100 || h > 250) {
          showError("Chiều cao không hợp lý! Vui lòng nhập chiều cao từ 100 cm đến 250 cm.", heightInput);
          return false;
        }

        if (isNaN(w) || w === null || weightInput.value.trim() === '') {
          showError("Vui lòng nhập cân nặng của bạn!", weightInput);
          return false;
        }
        if (w < 30 || w > 250) {
          showError("Cân nặng không hợp lý! Vui lòng nhập cân nặng từ 30 kg đến 250 kg.", weightInput);
          return false;
        }

        // Ràng buộc tương quan giữa Chiều cao và Cân nặng (Chỉ số BMI chuẩn sinh học)
        const bmiVal = w / ((h / 100) ** 2);
        if (bmiVal < 11) {
          showError(`Tỷ lệ cân nặng quá thấp so với chiều cao (BMI = ${bmiVal.toFixed(1)}). Vui lòng kiểm tra lại số đo!`, weightInput);
          return false;
        }
        if (bmiVal > 65) {
          showError(`Tỷ lệ cân nặng quá cao so với chiều cao (BMI = ${bmiVal.toFixed(1)}). Vui lòng kiểm tra lại số đo!`, weightInput);
          return false;
        }

        if (errBox) errBox.classList.add('hidden');
        return true;
      }

      if (step === 4) {
        const act = parseFloat(document.querySelector('input[name="act"]:checked')?.value);
        if (!act || isNaN(act)) {
          alert("Vui lòng chọn mức độ vận động hàng tuần!");
          return false;
        }
        return true;
      }

      return true;
    }

    // Xem trước chỉ số BMI động và cảnh báo tức thì khi người dùng gõ
    function updateStep3Preview() {
      const hInput = document.getElementById('inp-height');
      const wInput = document.getElementById('inp-weight');
      const bmiSpan = document.getElementById('step3-preview-bmi');
      const badgeSpan = document.getElementById('step3-preview-badge');
      const errBox = document.getElementById('step3-error-msg');
      const errText = document.getElementById('step3-error-text');

      if (!hInput || !wInput) return;
      const h = parseFloat(hInput.value);
      const w = parseFloat(wInput.value);

      if (!h || !w || isNaN(h) || isNaN(w) || h <= 0 || w <= 0) {
        if (bmiSpan) bmiSpan.innerText = "--";
        if (badgeSpan) {
          badgeSpan.innerText = "Chờ nhập đủ số đo";
          badgeSpan.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-200 text-slate-700";
        }
        return;
      }

      const hM = h / 100;
      const bmiVal = w / (hM * hM);
      if (bmiSpan) bmiSpan.innerText = bmiVal.toFixed(1);

      // Cảnh báo trực tiếp nếu ngoài khoảng hợp lý
      let warn = "";
      if (h < 100 || h > 250) warn = "Chiều cao người thông thường từ 100 - 250 cm.";
      else if (w < 30 || w > 250) warn = "Cân nặng thông thường từ 30 - 250 kg.";
      else if (bmiVal < 11 || bmiVal > 65) warn = `Chỉ số BMI dự tính (${bmiVal.toFixed(1)}) ngoài ngưỡng sinh học bình thường. Hãy kiểm tra lại số đo.`;

      if (warn && errBox && errText) {
        errText.innerText = warn;
        errBox.classList.remove('hidden');
      } else if (errBox) {
        errBox.classList.add('hidden');
      }

      if (badgeSpan) {
        if (bmiVal < 18.5) {
          badgeSpan.innerText = "Thiếu cân";
          badgeSpan.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200";
        } else if (bmiVal < 23.0) {
          badgeSpan.innerText = "Cân đối (Chuẩn châu Á)";
          badgeSpan.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200";
        } else if (bmiVal < 25.0) {
          badgeSpan.innerText = "Thừa cân";
          badgeSpan.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-orange-100 text-orange-800 border border-orange-200";
        } else {
          badgeSpan.innerText = "Béo phì";
          badgeSpan.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200";
        }
      }
    }

    async function nextStep() {
      if (!validateStep(currentStep)) {
        return;
      }
      if (currentStep < 4) {
        currentStep++;
        updateStepUI();
        if (currentStep === 3) updateStep3Preview();
      } else {
        if (await calculateAndApplyNutrition()) switchScreen('screen-dashboard');
      }
    }

    function prevStep() {
      if (currentStep > 1) {
        currentStep--;
        updateStepUI();
      } else {
        if (isEditingProfile) {
          switchScreen('screen-dashboard');
        } else {
          switchScreen('screen-auth');
        }
      }
    }

    function updateStepUI() {
      for (let i = 1; i <= 4; i++) {
        document.getElementById(`step-${i}`).classList.add('hidden');
      }
      document.getElementById(`step-${currentStep}`).classList.remove('hidden');
      document.getElementById('step-counter').innerText = `Bước ${currentStep} / 4`;
      document.getElementById('step-progress-bar').style.width = `${(currentStep / 4) * 100}%`;

      const btn = document.getElementById('btn-next-step');
      if (currentStep === 4) {
        btn.innerHTML = `<span>Hoàn tất</span><i data-lucide="check" class="w-4 h-4"></i>`;
      } else {
        btn.innerHTML = `<span>Tiếp tục</span><i data-lucide="chevron-right" class="w-4 h-4"></i>`;
      }
      lucide.createIcons();
    }

    function setGender(gender) {
      userProfile.gender = gender;
      const btnMale = document.getElementById('btn-male');
      const btnFemale = document.getElementById('btn-female');
      if (gender === 'male') {
        btnMale.className = "p-5 rounded-2xl border-2 border-brand-500 bg-emerald-50/50 flex items-center justify-center gap-3";
        btnFemale.className = "p-5 rounded-2xl border-2 border-slate-200 flex items-center justify-center gap-3";
      } else {
        btnFemale.className = "p-5 rounded-2xl border-2 border-brand-500 bg-emerald-50/50 flex items-center justify-center gap-3";
        btnMale.className = "p-5 rounded-2xl border-2 border-slate-200 flex items-center justify-center gap-3";
      }
      lucide.createIcons();
    }

    async function calculateAndApplyNutrition() {
      if (!Number.isInteger(userProfile.id) || userProfile.id <= 0) {
        showAuthAlert('Vui lòng đăng nhập trước khi lưu hồ sơ.');
        switchScreen('screen-auth');
        return false;
      }
      const fields = {
        gender: userProfile.gender,
        age: Number(document.getElementById('inp-age-range').value),
        height: Number(document.getElementById('inp-height').value),
        weight: Number(document.getElementById('inp-weight').value),
        activity_level: Number(document.querySelector('input[name="act"]:checked')?.value),
        goal: document.querySelector('input[name="goal"]:checked')?.value
      };
      const button = document.getElementById('btn-next-step');
      button.disabled = true;
      try {
        const calculated = await NutriFitAPI.calculateNutrition(fields);
        if (!calculated.success) { alert(calculated.message || 'Hồ sơ không hợp lệ.'); return false; }
        const saved = await NutriFitAPI.saveProfile({ user_id: userProfile.id, ...fields });
        if (!saved.success) { alert(saved.message || 'Chưa lưu được hồ sơ.'); return false; }
        const profile = await NutriFitAuth.loadProfile(userProfile.id);
        if (!profile) { alert('Đã lưu hồ sơ nhưng chưa tải được mục tiêu. Hãy thử lại.'); return false; }
        applyLoadedProfile(profile);
        saveSession(userProfile, profile);
        return true;
      } finally {
        button.disabled = false;
      }
    }
