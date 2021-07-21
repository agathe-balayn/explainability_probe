import { domain } from "./settings";
const auth = domain + "auth/";
const new_user = domain + "api/UserSECA/users/";
const see_all_images = domain + "api/SECAAlgo/Images/allImages";
const add_wiki = domain + "api/Wiki/add_wiki/";
const remove_wiki = domain + "api/Wiki/remove_wiki/";
const expertBackground = domain + "api/Wiki/expertBackground/";
const updateTitle_url = domain + "api/Wiki/updateTitleIntro/";
const data_overall_explanations =
  domain + "api/SECAAlgo/Explore/data_overall_explanations/";
const matrix_data = domain + "api/SECAAlgo/Matrix/matrix";
const matrix_images = domain + "api/SECAAlgo/Matrix/images";
const binary_query = domain + "api/SECAAlgo/Query/uquery/";
const query_rules_url = domain + "api/SECAAlgo/Query/query_rules/";
const query_concept_matrix_url = domain + "api/SECAAlgo/Query/query_concept_matrix/";
const query_specific_url = domain + "api/SECAAlgo/Query/query_specific/";
const notes_url = domain + "api/SECAAlgo/notes"
const expert_questions_url = domain + "api/Expert/questions/"
const get_all_predicitons_url = domain + "api/SECAAlgo/UserProfile/predictions"
const f1 = domain + "api/SECAAlgo/f1_scores/"
const get_sessions_url = domain + "api/UserSECA/get_sessions"
const add_image_url = domain + "api/SECAAlgo/add_image/"
const add_data_url = domain + "api/SECAAlgo/add_data/"
const algo_url = domain + "algo/"
const data_specific_explanations_url = domain + "api/SECAAlgo/Explore/data_specific_explanations/"

export {
  auth,
  new_user,
  see_all_images,
  add_wiki,
  remove_wiki,
  expertBackground,
  data_overall_explanations,
  matrix_data,
  matrix_images,
  binary_query,
  query_rules_url,
  query_specific_url,
  query_concept_matrix_url,
  updateTitle_url,
  notes_url,
  expert_questions_url,
  get_all_predicitons_url,
  f1,
  get_sessions_url,
  add_image_url,
  add_data_url,
  algo_url,
  data_specific_explanations_url
};
