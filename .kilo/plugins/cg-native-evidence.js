import { tool } from '@kilocode/plugin';
import { passiveTools } from '../plugin-support/cg-native-evidence/evidence.mjs';

/** Passive Kilo-only evidence tools. Startup registers no execution hooks. */
export default async function nativeEvidence(input) { return passiveTools(input, tool); }
