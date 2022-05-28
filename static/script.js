'use strict';


// Quan fem click sobre una paraula vermella mostrem una finestra (element HTML dialog)
function showwords(params, ctx, idx) {
  document.getElementsByClassName(idx)[1].showModal(); 
}

// Quan fem click sobre una paraula sugerida la corregim automaticament
function correctword(ctx, idx, parent) {
  ctx.parentNode.parentNode.parentNode.style="text-decoration: none; color:rgb(17, 127, 0); font-weight: 600"  ; 
  ctx.parentNode.parentNode.parentNode. innerHTML = ctx.innerHTML + " "
}

// Tanquem la finestra de sugerencies, aixo es farà quan donem click a `Close`
function closeModal(ctx) {
  console.log(ctx.parentNode)
  ctx.parentNode.close()
}