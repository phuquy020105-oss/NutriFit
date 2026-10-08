// NutriFit Frontend
// Extracted from the existing UI logic; behavior preserved.

    function applyLoadedProfile(p) {
      userProfile.gender = p.Gender || 'male';
      userProfile.age = p.Age || 24;
      userProfile.height = p.HeightCm || 172;
      userProfile.weight = p.WeightKg || 68;
      userProfile.goal = p.Goal || 'lose';
      userProfile.activity = p.ActivityLevel || 1.2;
      userProfile.bmr = p.Bmr || 1650;
      userProfile.tdee = p.Tdee || 1980;
      userProfile.targetKcal = p.TargetKcal || 1480;
      userProfile.carbs = p.TargetCarbs || 166;
      userProfile.protein = p.TargetProtein || 92;
      userProfile.fat = p.TargetFat || 49;
      userProfile.fiber = p.TargetFiber || 31;
      userProfile.waterTarget = p.TargetWaterMl || 2400;

      // Tính chính xác chỉ số BMI theo công thức khoa học: Cân nặng (kg) / [Chiều cao (m)]²
      const hM = (userProfile.height || 172) / 100;
      userProfile.bmi = (userProfile.weight / (hM * hM)).toFixed(1);

      // Điền ngược vào các trường Onboarding
      document.getElementById('inp-height').value = userProfile.height;
      document.getElementById('inp-weight').value = userProfile.weight;
      document.getElementById('age-val').innerText = `${userProfile.age} tuổi`;
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

    function nextStep() {
      if (!validateStep(currentStep)) {
        return;
      }
      if (currentStep < 4) {
        currentStep++;
        updateStepUI();
        if (currentStep === 3) updateStep3Preview();
      } else {
        calculateAndApplyNutrition();
        switchScreen('screen-dashboard');
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
      let h = parseFloat(document.getElementById('inp-height')?.value) || 172;
      let w = parseFloat(document.getElementById('inp-weight')?.value) || 68;
      let age = parseInt(document.getElementById('inp-age-range')?.value) || parseInt(document.getElementById('age-val')?.innerText) || 24;
      const goal = document.querySelector('input[name="goal"]:checked')?.value || 'lose';
      const act = parseFloat(document.querySelector('input[name="act"]:checked')?.value) || 1.2;

      // Giới hạn ràng buộc logic an toàn
      h = Math.min(Math.max(h, 100), 250);
      w = Math.min(Math.max(w, 30), 250);
      age = Math.min(Math.max(age, 12), 95);

      userProfile.height = h;
      userProfile.weight = w;
      userProfile.age = age;
      userProfile.goal = goal;
      userProfile.activity = act;

      let bmr = (10 * w) + (6.25 * h) - (5 * age);
      bmr = userProfile.gender === 'male' ? bmr + 5 : bmr - 161;

      const tdee = Math.round(bmr * act);
      let targetKcal = tdee;
      if (goal === 'lose') targetKcal = Math.round(tdee - 500);
      else if (goal === 'gain') targetKcal = Math.round(tdee + 350);

      const carbs = Math.round((targetKcal * 0.45) / 4);
      const protein = Math.round((targetKcal * 0.25) / 4);
      const fat = Math.round((targetKcal * 0.30) / 9);
      const fiber = Math.round(w * 0.45);
      const bmi = (w / ((h / 100) ** 2)).toFixed(1);
      const water = Math.round(w * 35);

      userProfile.targetKcal = targetKcal;
      userProfile.bmr = Math.round(bmr);
      userProfile.tdee = tdee;
      userProfile.carbs = carbs;
      userProfile.protein = protein;
      userProfile.fat = fat;
      userProfile.fiber = fiber;
      userProfile.bmi = bmi;
      userProfile.waterTarget = water;

      updateDashboardUI();

      // Cập nhật session với hồ sơ mới
      saveSession({ id: userProfile.id, email: userProfile.email, fullname: userProfile.fullname }, userProfile);

      // Lưu hồ sơ vào bảng UserProfiles trong SQL Server
      NutriFitAPI.saveProfile({
        userId: userProfile.id || 1,
        gender: userProfile.gender,
        age: userProfile.age,
        height: userProfile.height,
        weight: userProfile.weight,
        activity: userProfile.activity,
        goal: userProfile.goal,
        bmr: userProfile.bmr,
        tdee: userProfile.tdee,
        targetKcal: userProfile.targetKcal,
        carbs: userProfile.carbs,
        protein: userProfile.protein,
        fat: userProfile.fat,
        fiber: userProfile.fiber,
        waterTarget: userProfile.waterTarget
      }).then(res => {
        console.log("Kết quả lưu SQL Server:", res);
      });
    }
