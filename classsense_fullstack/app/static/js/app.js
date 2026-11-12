const $ = (id) => document.getElementById(id);
let currentSessionId = null;
let trendChart = null;
let studentsCache = [];

async function api(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Request failed.");
  return data;
}
function showAlert(message, isError = false) {
  const box = $("alert"); box.textContent = message;
  box.classList.remove("hidden", "error"); if (isError) box.classList.add("error");
  window.scrollTo({top: 0, behavior: "smooth"});
  setTimeout(() => box.classList.add("hidden"), 4500);
}
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
function dateText(value) { return new Date(value).toLocaleString([], {dateStyle:"medium",timeStyle:"short"}); }
function setView(name) {
  document.querySelectorAll(".view").forEach(v => v.classList.add("hidden"));
  $(name + "-view").classList.remove("hidden");
  document.querySelectorAll(".nav").forEach(n => n.classList.toggle("active", n.dataset.view === name));
  $("page-title").textContent = name === "overview" ? "Overview" : name === "sessions" ? "Sessions" : name === "students" ? "Students" : "Session workspace";
}
document.querySelectorAll(".nav").forEach(n => n.addEventListener("click", () => {setView(n.dataset.view); if(n.dataset.view==="sessions") loadSessions(); if(n.dataset.view==="students") loadStudents();}));
document.querySelectorAll("[data-go]").forEach(n => n.addEventListener("click", () => {setView(n.dataset.go);loadSessions();}));
function openModal(id){$(id).classList.remove("hidden")}
document.querySelectorAll("[data-close]").forEach(b=>b.addEventListener("click",()=>b.closest(".modal").classList.add("hidden")));
["new-session-open","new-session-open-2"].forEach(id=>$(id).addEventListener("click",()=>openModal("session-modal")));
$("add-student-open").addEventListener("click",()=>openModal("student-modal"));
$("session-form").addEventListener("submit",async e=>{
 e.preventDefault();const f=new FormData(e.target);
 try{const result=await api("/api/sessions",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(Object.fromEntries(f))});e.target.reset();$("session-modal").classList.add("hidden");showAlert("Session created.");await openSession(result.id);}
 catch(err){showAlert(err.message,true)}
});
$("student-form").addEventListener("submit",async e=>{
 e.preventDefault();const f=new FormData(e.target);
 try{await api("/api/students",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(Object.fromEntries(f))});e.target.reset();$("student-modal").classList.add("hidden");showAlert("Student added to roster.");loadStudents();loadDashboard();}
 catch(err){showAlert(err.message,true)}
});
async function loadDashboard(){
 try{
  const d=await api("/api/dashboard");$("stat-students").textContent=d.active_students;$("stat-active").textContent=d.active_sessions;$("stat-total").textContent=d.total_sessions;
  $("recent-table").innerHTML=d.recent_sessions.length?d.recent_sessions.map(s=>`<tr><td><b>${escapeHtml(s.title)}</b></td><td>${escapeHtml(s.class_name)}</td><td>${dateText(s.started_at)}</td><td>${s.present} present</td><td><span class="pill ${s.status!=="active"?"gray":""}">${escapeHtml(s.status)}</span></td><td><button class="btn btn-quiet" onclick="openSession(${s.id})">Open →</button></td></tr>`).join(""):`<tr><td colspan="6" class="empty">No sessions yet. Create your first session.</td></tr>`;
 }catch(e){showAlert(e.message,true)}
}
async function loadStudents(){
 try{studentsCache=await api("/api/students");$("students-table").innerHTML=studentsCache.map(s=>`<tr><td><b>${escapeHtml(s.full_name)}</b></td><td>${escapeHtml(s.student_code)}</td><td>${escapeHtml(s.group_name)}</td><td><span class="pill">${s.active?"Active":"Inactive"}</span></td></tr>`).join("")||`<tr><td colspan="4" class="empty">No students in roster.</td></tr>`;}
 catch(e){showAlert(e.message,true)}
}
async function loadSessions(){
 try{const items=await api("/api/sessions");$("sessions-list").innerHTML=items.map(s=>`<article class="session-card" onclick="openSession(${s.id})"><span class="pill ${s.status!=="active"?"gray":""}">${escapeHtml(s.status)}</span><h3>${escapeHtml(s.title)}</h3><p>${escapeHtml(s.class_name)} · ${dateText(s.started_at)}</p><div class="session-meta"><span>${s.present} attendance records marked present</span><b>Open →</b></div></article>`).join("")||`<div class="panel empty">No sessions created yet.</div>`;}
 catch(e){showAlert(e.message,true)}
}
async function openSession(id){
 currentSessionId=id;setView("session-detail");
 try{
  const sessions=await api("/api/sessions");const s=sessions.find(x=>x.id===id);
  if(!s)throw new Error("Session not found.");
  $("detail-title").textContent=s.title;$("detail-subtitle").textContent=`${s.class_name} · Started ${dateText(s.started_at)} · ${s.status}`;
  $("end-session").classList.toggle("hidden",s.status!=="active");
  await loadStudents();
  $("attendance-student").innerHTML=studentsCache.filter(x=>x.active).map(x=>`<option value="${x.id}">${escapeHtml(x.full_name)} (${escapeHtml(x.student_code)})</option>`).join("");
  await Promise.all([loadAttendance(),loadInsights()]);
 }catch(e){showAlert(e.message,true)}
}
async function loadAttendance(){
 const rows=await api(`/api/sessions/${currentSessionId}/attendance`);
 $("attendance-table").innerHTML=rows.map(a=>`<tr><td><b>${escapeHtml(a.full_name)}</b><br><small>${escapeHtml(a.student_code)}</small></td><td><span class="pill">${escapeHtml(a.status)}</span></td><td>${dateText(a.marked_at)}</td></tr>`).join("")||`<tr><td colspan="3" class="empty">No attendance marked yet.</td></tr>`;
}
$("mark-attendance").addEventListener("click",async()=>{
 const student_id=Number($("attendance-student").value);if(!student_id)return showAlert("Add students to the roster first.",true);
 try{await api(`/api/sessions/${currentSessionId}/attendance`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({student_id,status:"present"})});showAlert("Attendance saved.");await loadAttendance();loadDashboard();}
 catch(e){showAlert(e.message,true)}
});
$("add-signal").addEventListener("click",async()=>{
 const payload={minute:$("signal-minute").value,value:$("signal-value").value,signal_type:$("signal-type").value};
 try{await api(`/api/sessions/${currentSessionId}/signals`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});showAlert("Session indicator saved.");await loadInsights();}
 catch(e){showAlert(e.message,true)}
});
async function loadInsights(){
 const d=await api(`/api/sessions/${currentSessionId}/insights`);
 $("suggestions").innerHTML=d.suggestions.map(s=>`<div class="suggestion">${escapeHtml(s)}</div>`).join("");
 $("no-chart").classList.toggle("hidden",d.timeline.length>0);
 if(trendChart)trendChart.destroy();
 if(d.timeline.length){
  trendChart=new Chart($("trend-chart"),{type:"line",data:{labels:d.timeline.map(x=>`Min ${x.minute}`),datasets:[{label:"Indicator score",data:d.timeline.map(x=>x.score),borderColor:"#587cf0",backgroundColor:"#587cf022",fill:true,tension:.35,pointRadius:4}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{y:{min:0,max:100,ticks:{stepSize:20}},x:{grid:{display:false}}}}});
 }
}
$("end-session").addEventListener("click",async()=>{
 if(!confirm("Complete this session?"))return;
 try{await api(`/api/sessions/${currentSessionId}/end`,{method:"POST"});showAlert("Session completed.");await openSession(currentSessionId);loadDashboard();}
 catch(e){showAlert(e.message,true)}
});
$("back-sessions").addEventListener("click",()=>{setView("sessions");loadSessions()});
$("upload-form").addEventListener("submit",async e=>{
 e.preventDefault();const file=$("upload-file").files[0];if(!file)return;
 const data=new FormData();data.append("file",file);
 try{const result=await api(`/api/sessions/${currentSessionId}/uploads`,{method:"POST",body:data});showAlert(result.message);e.target.reset();}
 catch(err){showAlert(err.message,true)}
});
loadDashboard();
