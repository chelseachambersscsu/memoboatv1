
// Utility functions for showing/hiding states and resetting form

function show(id) {
  document.getElementById(id).classList.remove("d-none");
}

function hide(id) {
  document.getElementById(id).classList.add("d-none");
}

function clearNotes() {
  document.getElementById("rawNotes").value = "";
}

function resetResults() {
  hide("resultsState");
  hide("errorState");
  hide("loadingState");
  show("placeholderState");
  document.getElementById("submitBtn").disabled = false;
}

// Rendering results from API response

function renderResults(data) {
  const today = new Date().toLocaleDateString("en-US", {
    month: "long", day: "numeric", year: "numeric"
  });
  document.getElementById("memoDate").textContent = today;
  document.getElementById("summaryText").textContent = data.summary;

  const actionList = document.getElementById("actionItemsList");
  actionList.innerHTML = "";
  data.action_items.forEach(function(item) {
    const li = document.createElement("li");
    const cb = document.createElement("input");
    cb.type = "checkbox";
    const label = document.createElement("span");
    label.textContent = item;
    cb.addEventListener("change", function() {
      li.classList.toggle("checked", cb.checked);
    });
    li.appendChild(cb);
    li.appendChild(label);
    actionList.appendChild(li);
  });

  const decisionList = document.getElementById("decisionsList");
  decisionList.innerHTML = "";
  data.key_decisions.forEach(function(decision) {
    const li = document.createElement("li");
    li.textContent = decision;
    decisionList.appendChild(li);
  });
}

// Download the memo as a text file

function downloadMemo() {
  const title   = document.getElementById("memoTitle").textContent;
  const date    = document.getElementById("memoDate").textContent;
  const summary = document.getElementById("summaryText").textContent;

  const actionItems = [];
  document.querySelectorAll("#actionItemsList li span").forEach(function(span) {
    actionItems.push("- " + span.textContent);
  });

  const decisions = [];
  document.querySelectorAll("#decisionsList li").forEach(function(li) {
    decisions.push("- " + li.textContent);
  });

  const content = [
    title,
    "Date: " + date,
    "",
    "SUMMARY",
    summary,
    "",
    "ACTION ITEMS",
    actionItems.join("\n"),
    "",
    "KEY DECISIONS",
    decisions.join("\n")
  ].join("\n");

  const blob = new Blob([content], { type: "text/plain" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = "memo.txt";
  a.click();
  URL.revokeObjectURL(url);
}

// Main function to process the meeting notes and call the API

async function processMemo() {
  const notes    = document.getElementById("rawNotes").value.trim();
  const typeId   = document.getElementById("meetingType").value;

  if (!notes) {
    alert("Please paste or type your meeting notes first.");
    return;
  }

  hide("placeholderState");
  hide("resultsState");
  hide("errorState");
  show("loadingState");
  document.getElementById("submitBtn").disabled = true;

  try {
    const response = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes: notes, type_id: typeId })
    });

    if (!response.ok) {
      throw new Error("Request failed — status " + response.status);
    }

    const data = await response.json();
    const raw  = data.choices[0].message.content;
    const memo = JSON.parse(raw);

    hide("loadingState");
    renderResults(memo);
    show("resultsState");
    document.getElementById("submitBtn").disabled = false;

  } catch (err) {
    hide("loadingState");
    document.getElementById("errorText").textContent =
      "Something went wrong: " + err.message;
    show("errorState");
    document.getElementById("submitBtn").disabled = false;
  }
}