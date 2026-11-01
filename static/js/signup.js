(() => {
  const username = document.querySelector("[data-username-input]");
  const box = document.querySelector("[data-suggestion-box]");
  if (!username || !box) return;

  const params = new URLSearchParams(window.location.search);
  const role = params.get("role") || document.querySelector('input[name="role"]')?.value;
  const nameField = {
    student: "student_name",
    teacher: "full_name",
    parent: "parent_name",
  }[role];
  const name = document.querySelector(`[name="${nameField}"]`);
  const block = document.querySelector('[name="block"]');
  const district = document.querySelector('[name="district"]');
  const message = box.querySelector("[data-suggestion-message]");
  const choice = box.querySelector("[data-suggestion-choice]");
  let timer;
  let sequence = 0;

  const update = () => {
    window.clearTimeout(timer);
    const fullName = name?.value.trim();
    if (!fullName) {
      box.hidden = true;
      return;
    }
    timer = window.setTimeout(async () => {
      const requestId = ++sequence;
      const query = new URLSearchParams({ name: fullName, block: block?.value.trim() || "", district: district?.value.trim() || "" });
      try {
        const response = await fetch(`/signup/username-suggestion/?${query}`);
        if (!response.ok) throw new Error("Suggestion unavailable");
        const data = await response.json();
        if (requestId !== sequence || !data.username) return;
        message.textContent = "Suggested username:";
        choice.textContent = data.username;
        box.hidden = false;
      } catch {
        box.hidden = true;
      }
    }, 250);
  };

  [name, block, district].filter(Boolean).forEach((field) => field.addEventListener("input", update));
  choice.addEventListener("click", () => {
    username.value = choice.textContent;
    username.dispatchEvent(new Event("input", { bubbles: true }));
    username.focus();
  });
  update();
})();
