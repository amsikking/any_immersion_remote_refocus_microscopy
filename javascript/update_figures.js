function update_figure_3() {
  var objectives = document.getElementById("figure_3_choice_objectives").value;
  var scale = document.getElementById("figure_3_choice_scale").value;
  if ((scale === "")){
  var filename = "./figures/sf_and_rr_range/sf_range" + objectives + scale + ".png";}
  if ((scale === "_log")){
  var filename = "./figures/sf_and_rr_range/sf_range" + objectives + scale + ".png";}
  var img = document.getElementById("fig_3_png");
  img.src = filename;
}

function update_figure_4() {
  var objectives = document.getElementById("figure_4_choice_objectives").value;
  var scale = document.getElementById("figure_4_choice_scale").value;
  if ((scale === "")){
  var filename = "./figures/sf_and_rr_range/sf_and_rr_range" + objectives + scale + ".png";}
  if ((scale === "_log")){
  var filename = "./figures/sf_and_rr_range/sf_and_rr_range" + objectives + scale + ".png";}
  var img = document.getElementById("fig_4_png");
  img.src = filename;
}
