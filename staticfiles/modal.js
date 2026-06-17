function showModal() {
  document.getElementById('my-drawer-4').click();
}

function add_activity(id) {
  document.getElementById('operation_plan_id').value = id
  document.getElementById('my_modal_2').showModal()
}

function edit_detail_activity() {
  document.getElementById('my_modal_2').showModal()
}

function closeModal() {
  const modal = document.getElementById("modal");
  modal.classList.remove("modal-open");
}

function show(id) {
  let sections = document.getElementsByClassName("section")
  for (const section of sections) {
    section.classList.add("hidden")
  }
  document.getElementById(id).classList.remove("hidden")
}
