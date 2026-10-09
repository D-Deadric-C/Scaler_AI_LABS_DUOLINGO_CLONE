/** Horizontal offsets (px from the path centre) that make nodes wind down the page. */
export const ZIGZAG = [0, 45, 70, 45, 0, -45, -70, -45] as const;

export const offsetFor = (index: number): number => ZIGZAG[index % ZIGZAG.length];

export type UnitTheme = { banner: string; node: string; shade: string };

/** Banner and node colours per unit (unit 1 pairs with the brown guide bear). Other units fall back to the unit's own colour. */
const THEMES: Record<number, UnitTheme> = {
  1: { banner: "#f49002", node: "#d38a45", shade: "#a96e38" },
  2: { banner: "#1da9ec", node: "#1da9ec", shade: "#1788bd" },
};

export function unitTheme(position: number, color: string): UnitTheme {
  return THEMES[position] ?? { banner: color, node: color, shade: `color-mix(in srgb, ${color} 70%, black)` };
}
