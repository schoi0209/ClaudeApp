import { loadFont as loadFraunces } from "@remotion/google-fonts/Fraunces";
import { loadFont as loadDMSans } from "@remotion/google-fonts/DMSans";

// Load Fraunces – both normal and italic weights
const frauncesNormal = loadFraunces("normal", {
  weights: ["300", "400", "700", "900"],
  subsets: ["latin"],
});
loadFraunces("italic", {
  weights: ["300", "400", "700", "900"],
  subsets: ["latin"],
});

const dmSansNormal = loadDMSans("normal", {
  weights: ["300", "400", "500", "700"],
  subsets: ["latin"],
});

export const frauncesFont = frauncesNormal.fontFamily; // "Fraunces"
export const dmSansFont = dmSansNormal.fontFamily;     // "DM Sans"
