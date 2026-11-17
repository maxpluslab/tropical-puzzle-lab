// Site footer with the project's credits, shared by the gallery and the explanation pages.
const base = import.meta.env.BASE_URL;

export const REPOSITORY = 'https://github.com/maxpluslab/tropical-puzzle-lab';
export const ORGANIZATION = 'https://github.com/maxpluslab';

export function footerHtml(): string {
  return `<footer class="foot">
    <p>Tropical Puzzle Lab is a <a href="${ORGANIZATION}">MaxPlusLab</a> project by Igor Kuvychko and Madeline V. Brandt.
    An experimental tool for studying puzzle construction and difficulty.</p>
    <p><a href="${base}">Gallery</a> ·
    <a href="${base}?page=math">The mathematics</a> ·
    <a href="${base}?page=difficulty">How difficulty is rated</a> ·
    <a href="${base}?page=print">Make a physical puzzle</a> ·
    <a href="${REPOSITORY}">Source on GitHub</a></p>
  </footer>`;
}
