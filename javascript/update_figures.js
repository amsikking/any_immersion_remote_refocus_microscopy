function update_figure_5() {
  var objectives = document.getElementById("figure_5_choice_objectives").value;
  var scale = document.getElementById("figure_5_choice_scale").value;
  if ((scale === "")){
  var filename = "./figures/sf_and_rr_depth/sf_depth" + objectives + scale + ".png";}
  if ((scale === "_log")){
  var filename = "./figures/sf_and_rr_depth/sf_depth" + objectives + scale + ".png";}
  var img = document.getElementById("fig_5_png");
  img.src = filename;
}

function update_figure_6() {
  var objectives = document.getElementById("figure_6_choice_objectives").value;
  var scale = document.getElementById("figure_6_choice_scale").value;
  if ((scale === "")){
  var filename = "./figures/sf_and_rr_depth/sf_and_rr_depth" + objectives + scale + ".png";}
  if ((scale === "_log")){
  var filename = "./figures/sf_and_rr_depth/sf_and_rr_depth" + objectives + scale + ".png";}
  var img = document.getElementById("fig_6_png");
  img.src = filename;
}

function update_figure_7() {
  var number = document.getElementById("figure_7_choice").value;
  if ((number === "1")){
  var filename = "./figures/zoom_lens/optics/output.gif";}
  if ((number === "2")){
  var filename = "./figures/zoom_lens/optics/output_reversed.gif";}
  var img = document.getElementById("fig_7_gif");
  img.src = filename;
}

function update_figure_A2() {
  var config = document.getElementById("figure_A2_choice_configuration").value;
  var figure = document.getElementById("figure_A2_choice_figure").value;
  if ((config === "_config_8")){
  var filename = "./figures/zoom_lens/optics/performance/" + figure + config + ".png";}
  if ((config === "_config_1")){
  var filename = "./figures/zoom_lens/optics/performance/" + figure + config + ".png";}
  var img = document.getElementById("fig_A2_png");
  img.src = filename;
}

function update_figure_A4() {
  var number = document.getElementById("figure_A4_choice_sheet").value;
  if ((number === "1")){
  var filename = "./figures/zoom_lens/mechanics/images/zoom_lens_132.5-150mm_sheet_" + number + ".png";}
  if ((number === "2")){
  var filename = "./figures/zoom_lens/mechanics/images/zoom_lens_132.5-150mm_sheet_" + number + ".png";}
  if ((number === "3")){
  var filename = "./figures/zoom_lens/mechanics/images/zoom_lens_132.5-150mm_sheet_" + number + ".png";}
  if ((number === "4")){
  var filename = "./figures/zoom_lens/mechanics/images/zoom_lens_132.5-150mm_sheet_" + number + ".png";}
  if ((number === "5")){
  var filename = "./figures/zoom_lens/mechanics/images/zoom_lens_132.5-150mm_sheet_" + number + ".png";}
  var img = document.getElementById("fig_A4_png");
  img.src = filename;
}

function update_figure_A5() {
  var number = document.getElementById("figure_A5_choice").value;
  if ((number === "1")){
  var filename = "./figures/zoom_lens/testing/FFP_speckle.mp4";}
  if ((number === "2")){
  var filename = "./figures/zoom_lens/testing/BFP_speckle.mp4";}
  var img = document.getElementById("fig_A5_mp4");
  img.src = filename;
}
