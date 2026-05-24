"use client";

import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  Treemap,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import {
  RADAR_COLORS,
  allocationDonutData,
  categoryStackedBarData,
  exposureBreakdown,
  portfolioFactsTable,
  portfolioSummary,
  portfolioTreemap,
  radarChartData,
  radarComparison,
  scatterRiskReturn,
  sectorHeatmap,
  stackedBarFundKeys,
  toPortfolioContext,
} from "@/lib/portfolioInsights/mockData";
import { useInsights } from "@/lib/insights/useInsights";
import { GlassCard } from "./GlassCard";
import { InsightsPageHeader } from "./InsightsPageHeader";

const CHART_GRID = "#2A3444";
const CHART_AXIS = "#8B95A8";
const ACCENT = "#00D09C";

type Props = {
  onBack: () => void;
  onMenuClick?: () => void;
  showMenu?: boolean;
};

export function PortfolioAnalysisPage({ onBack, onMenuClick, showMenu }: Props) {
  const { funds, portfolioHoldings, disclaimer, lastUpdated, loading, fromApi, error } = useInsights();
  const ctx = useMemo(
    () => toPortfolioContext(funds, portfolioHoldings),
    [funds, portfolioHoldings]
  );

  const summary = useMemo(() => portfolioSummary(ctx), [ctx]);
  const donut = useMemo(() => allocationDonutData(ctx), [ctx]);
  const treemap = useMemo(() => portfolioTreemap(ctx), [ctx]);
  const stacked = useMemo(() => categoryStackedBarData(ctx), [ctx]);
  const fundKeys = useMemo(() => stackedBarFundKeys(ctx), [ctx]);
  const scatter = useMemo(() => scatterRiskReturn(ctx), [ctx]);
  const heatmap = useMemo(() => sectorHeatmap(ctx), [ctx]);
  const radarAll = useMemo(() => radarComparison(ctx), [ctx]);
  const facts = useMemo(() => portfolioFactsTable(ctx), [ctx]);
  const exposure = useMemo(() => exposureBreakdown(ctx), [ctx]);

  const [radarIds, setRadarIds] = useState<string[]>(["flexicap", "defence", "gold", "elss"]);

  const radarSeries = useMemo(
    () => radarAll.filter((s) => radarIds.includes(s.fundId)),
    [radarAll, radarIds]
  );
  const radarData = useMemo(() => radarChartData(radarSeries), [radarSeries]);

  const summaryCards = [
    { label: "Total Funds", value: String(summary.totalFunds) },
    { label: "Equity Exposure", value: `${summary.equityPct}%` },
    { label: "Gold Exposure", value: `${summary.goldPct}%` },
    { label: "Silver Exposure", value: `${summary.silverPct}%` },
    { label: "Fund Categories", value: String(summary.categoryCount) },
    { label: "Thematic Funds", value: String(summary.thematicCount) },
  ];

  if (loading) {
    return (
      <div className="flex min-h-0 flex-1 flex-col items-center justify-center text-app-muted">
        Loading portfolio breakdown…
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <InsightsPageHeader
        title="Portfolio Breakdown"
        subtitle={
          fromApi
            ? `Corpus synced · last updated ${lastUpdated || "—"}`
            : "Offline fallback · illustrative mock data"
        }
        onBack={onBack}
        onMenuClick={onMenuClick}
        showMenu={showMenu}
      />

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-6 sm:px-8">
        <div className="mx-auto max-w-7xl space-y-8">
          <FactsBanner text={disclaimer} apiError={error} fromApi={fromApi} lastUpdated={lastUpdated} />

          <section>
            <SectionTitle>Portfolio summary</SectionTitle>
            <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
              {summaryCards.map((item) => (
                <GlassCard key={item.label}>
                  <p className="text-xs font-medium uppercase tracking-wide text-app-muted">{item.label}</p>
                  <p className="mt-2 text-xl font-semibold text-app-text">{item.value}</p>
                </GlassCard>
              ))}
            </div>
          </section>

          <section className="space-y-6">
            <SectionTitle>Visual charts</SectionTitle>
            <div className="grid gap-6 xl:grid-cols-2">
              <GlassCard>
                <ChartHeader
                  title="Asset allocation"
                  subtitle="Equity vs gold vs silver (mock weights)"
                />
                <ChartBox height={280}>
                  <PieChart>
                    <Pie
                      data={donut}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={72}
                      outerRadius={110}
                      paddingAngle={3}
                      stroke="transparent"
                    >
                      {donut.map((entry) => (
                        <Cell key={entry.name} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip content={<DonutTooltip />} />
                    <Legend />
                  </PieChart>
                </ChartBox>
              </GlassCard>

              <GlassCard>
                <ChartHeader title="Portfolio composition" subtitle="Category hierarchy treemap" />
                <ChartBox height={280}>
                  <Treemap
                    data={treemap.children ?? []}
                    dataKey="size"
                    nameKey="name"
                    stroke="#1a2332"
                    fill={ACCENT}
                    content={<TreemapTile />}
                  />
                </ChartBox>
              </GlassCard>

              <GlassCard className="xl:col-span-2">
                <ChartHeader title="Category distribution" subtitle="Stacked weight by fund category" />
                <ChartBox height={300}>
                  <BarChart data={stacked} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                    <CartesianGrid stroke={CHART_GRID} strokeDasharray="3 3" />
                    <XAxis dataKey="category" tick={{ fill: CHART_AXIS, fontSize: 11 }} />
                    <YAxis tick={{ fill: CHART_AXIS, fontSize: 10 }} unit="%" />
                    <Tooltip content={<StackTooltip fundKeys={fundKeys} />} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    {fundKeys.map((key, i) => (
                      <Bar
                        key={key}
                        dataKey={key}
                        stackId="portfolio"
                        fill={RADAR_COLORS[i % RADAR_COLORS.length]}
                        radius={i === fundKeys.length - 1 ? [4, 4, 0, 0] : undefined}
                      />
                    ))}
                  </BarChart>
                </ChartBox>
              </GlassCard>

              <GlassCard>
                <ChartHeader
                  title="Risk vs return scatter"
                  subtitle="Historical metrics · informational only"
                />
                <ChartBox height={280}>
                  <ScatterChart margin={{ top: 12, right: 12, bottom: 8, left: 0 }}>
                    <CartesianGrid stroke={CHART_GRID} strokeDasharray="3 3" />
                    <XAxis
                      type="number"
                      dataKey="risk"
                      name="Volatility index"
                      tick={{ fill: CHART_AXIS, fontSize: 10 }}
                      label={{ value: "Volatility index", position: "insideBottom", offset: -4, fill: CHART_AXIS, fontSize: 10 }}
                    />
                    <YAxis
                      type="number"
                      dataKey="return1Y"
                      name="1Y return"
                      tick={{ fill: CHART_AXIS, fontSize: 10 }}
                      unit="%"
                      label={{ value: "1Y return %", angle: -90, position: "insideLeft", fill: CHART_AXIS, fontSize: 10 }}
                    />
                    <ZAxis range={[80, 80]} />
                    <Tooltip content={<ScatterTooltip />} cursor={{ strokeDasharray: "3 3" }} />
                    <Scatter data={scatter} fill={ACCENT}>
                      {scatter.map((_, i) => (
                        <Cell key={scatter[i].name} fill={RADAR_COLORS[i % RADAR_COLORS.length]} />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ChartBox>
                <p className="mt-2 text-xs text-app-muted">
                  Each point represents a scheme&apos;s historical 1Y return and a mock volatility index.
                </p>
              </GlassCard>

              <GlassCard>
                <ChartHeader title="Sector exposure heatmap" subtitle="Weighted sector intensity (mock)" />
                <SectorHeatmap sectors={heatmap} />
              </GlassCard>

              <GlassCard className="xl:col-span-2">
                <ChartHeader title="Multi-metric radar" subtitle="Normalized comparison across selected funds" />
                <RadarFundPicker
                  selected={radarIds}
                  onToggle={(id) =>
                    setRadarIds((prev) =>
                      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 5 ? [...prev, id] : prev
                    )
                  }
                />
                <ChartBox height={320}>
                  <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
                    <PolarGrid stroke={CHART_GRID} />
                    <PolarAngleAxis dataKey="metric" tick={{ fill: CHART_AXIS, fontSize: 11 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: CHART_AXIS, fontSize: 9 }} />
                    <Tooltip content={<RadarTooltip series={radarSeries} />} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    {radarSeries.map((s, i) => (
                      <Radar
                        key={s.fundId}
                        name={s.name}
                        dataKey={s.name}
                        stroke={RADAR_COLORS[i % RADAR_COLORS.length]}
                        fill={RADAR_COLORS[i % RADAR_COLORS.length]}
                        fillOpacity={0.2}
                        strokeWidth={2}
                      />
                    ))}
                  </RadarChart>
                </ChartBox>
              </GlassCard>
            </div>
          </section>

          <section>
            <SectionTitle>Portfolio facts</SectionTitle>
            <GlassCard className="mt-4 overflow-x-auto p-0">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead>
                  <tr className="border-b border-app-border bg-app-bg/40 text-xs uppercase tracking-wide text-app-muted">
                    <th className="px-4 py-3 font-semibold">Fund</th>
                    <th className="px-4 py-3 font-semibold">Weight</th>
                    <th className="px-4 py-3 font-semibold">Category</th>
                    <th className="px-4 py-3 font-semibold">Expense</th>
                    <th className="px-4 py-3 font-semibold">1Y Return</th>
                    <th className="px-4 py-3 font-semibold">Risk</th>
                    <th className="px-4 py-3 font-semibold">Benchmark</th>
                    <th className="px-4 py-3 font-semibold">Asset class</th>
                  </tr>
                </thead>
                <tbody>
                  {facts.map((row) => (
                    <tr
                      key={row.fundId}
                      className="border-b border-app-border/50 transition hover:bg-groww/5"
                    >
                      <td className="px-4 py-3 font-medium text-app-text">{row.name}</td>
                      <td className="px-4 py-3 text-app-text">{row.weightPct}%</td>
                      <td className="px-4 py-3 text-app-muted">{row.category}</td>
                      <td className="px-4 py-3 text-app-text">{row.expenseRatio}%</td>
                      <td className="px-4 py-3 text-app-text">{row.return1Y}%</td>
                      <td className="px-4 py-3 text-app-muted">{row.risk}</td>
                      <td className="max-w-[140px] truncate px-4 py-3 text-app-muted" title={row.benchmark}>
                        {row.benchmark}
                      </td>
                      <td className="px-4 py-3 text-app-text">{row.assetClass}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </GlassCard>
          </section>

          <section>
            <SectionTitle>Exposure breakdown</SectionTitle>
            <div className="mt-4 grid gap-6 lg:grid-cols-2">
              <GlassCard>
                <h4 className="text-sm font-semibold text-groww/90">Allocation summary</h4>
                <dl className="mt-4 space-y-3 text-sm">
                  <ExposureRow label="Equity allocation" value={`${exposure.equityAllocationPct}%`} />
                  <ExposureRow label="Commodity allocation" value={`${exposure.commodityAllocationPct}%`} />
                  <ExposureRow
                    label="Thematic / sectoral schemes"
                    value={String(exposure.thematicFunds.length)}
                  />
                </dl>
              </GlassCard>

              <GlassCard>
                <h4 className="text-sm font-semibold text-groww/90">Category distribution</h4>
                <ul className="mt-4 space-y-2">
                  {exposure.categoryDistribution.map((c) => (
                    <li key={c.category} className="flex items-center justify-between text-sm">
                      <span className="text-app-muted">{c.category}</span>
                      <span className="font-medium text-app-text">{c.weightPct}%</span>
                    </li>
                  ))}
                </ul>
              </GlassCard>

              <GlassCard className="lg:col-span-2">
                <h4 className="text-sm font-semibold text-groww/90">Thematic & sectoral holdings</h4>
                <div className="mt-4 flex flex-wrap gap-2">
                  {exposure.thematicFunds.map((t) => (
                    <span
                      key={t.name}
                      className="rounded-full border border-app-border bg-app-bg/50 px-3 py-1.5 text-xs text-app-text"
                    >
                      {t.name} · {t.weightPct}%
                    </span>
                  ))}
                </div>
                <p className="mt-4 text-xs text-app-muted">
                  Category labels reflect scheme factsheets. This view does not evaluate portfolio quality.
                </p>
              </GlassCard>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function FactsBanner({
  text,
  apiError,
  fromApi,
  lastUpdated,
}: {
  text: string;
  apiError: string | null;
  fromApi: boolean;
  lastUpdated: string;
}) {
  return (
    <div className="space-y-1 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100/90">
      <p>{text}</p>
      {fromApi && lastUpdated ? (
        <p className="text-xs text-amber-200/70">Scheme facts last updated: {lastUpdated}</p>
      ) : null}
      {apiError ? <p className="text-xs text-amber-200/60">API unavailable — showing fallback data.</p> : null}
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h3 className="text-base font-semibold text-app-text">{children}</h3>;
}

function ChartHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="mb-3">
      <p className="font-semibold text-app-text">{title}</p>
      <p className="text-xs text-app-muted">{subtitle}</p>
    </div>
  );
}

function ChartBox({ height, children }: { height: number; children: React.ReactNode }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      {children as React.ReactElement}
    </ResponsiveContainer>
  );
}

function ExposureRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-app-border/40 pb-2">
      <dt className="text-app-muted">{label}</dt>
      <dd className="font-medium text-app-text">{value}</dd>
    </div>
  );
}

function SectorHeatmap({ sectors }: { sectors: { sector: string; intensity: number }[] }) {
  const max = Math.max(...sectors.map((s) => s.intensity), 1);
  return (
    <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
      {sectors.map(({ sector, intensity }) => {
        const t = intensity / max;
        return (
          <div
            key={sector}
            className="rounded-xl border border-white/5 p-3 text-center transition hover:scale-[1.02]"
            style={{ backgroundColor: `rgba(0, 208, 156, ${0.08 + t * 0.35})` }}
          >
            <p className="text-xs text-app-muted">{sector}</p>
            <p className="mt-1 text-lg font-semibold text-app-text">{intensity}%</p>
          </div>
        );
      })}
    </div>
  );
}

function RadarFundPicker({
  selected,
  onToggle,
}: {
  selected: string[];
  onToggle: (id: string) => void;
}) {
  const ids = [
    { id: "flexicap", label: "Flexi Cap" },
    { id: "midcap", label: "Mid Cap" },
    { id: "smallcap", label: "Small Cap" },
    { id: "elss", label: "ELSS" },
    { id: "defence", label: "Defence" },
    { id: "pharma", label: "Pharma" },
    { id: "manufacturing", label: "Mfg" },
    { id: "gold", label: "Gold" },
    { id: "silver", label: "Silver" },
  ];

  return (
    <div className="mb-3 flex flex-wrap gap-1">
      {ids.map(({ id, label }) => (
        <button
          key={id}
          type="button"
          onClick={() => onToggle(id)}
          className={`rounded-md px-2.5 py-1 text-xs font-medium transition ${
            selected.includes(id) ? "bg-groww/20 text-groww" : "text-app-muted hover:bg-app-surface"
          }`}
        >
          {label}
        </button>
      ))}
      <span className="self-center px-1 text-[10px] text-app-muted">(max 5)</span>
    </div>
  );
}

function TreemapTile(props: {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  name?: string;
  value?: number;
  index?: number;
}) {
  const { x = 0, y = 0, width = 0, height = 0, name = "", index = 0 } = props;
  if (width < 4 || height < 4) return null;
  const fill = RADAR_COLORS[index % RADAR_COLORS.length];
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={fill}
        fillOpacity={0.75}
        stroke="#0f1419"
        strokeWidth={2}
        rx={4}
        className="transition-opacity hover:opacity-90"
      />
      {width > 48 && height > 28 ? (
        <text x={x + 6} y={y + 18} fill="#fff" fontSize={11} fontWeight={600}>
          {name}
        </text>
      ) : null}
      {width > 48 && height > 44 ? (
        <text x={x + 6} y={y + 32} fill="rgba(255,255,255,0.75)" fontSize={10}>
          {props.value}%
        </text>
      ) : null}
    </g>
  );
}

function DonutTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { name: string; value: number; payload: { fill: string } }[];
}) {
  if (!active || !payload?.length) return null;
  const p = payload[0];
  return (
    <div className="rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs shadow-xl">
      <p className="font-semibold" style={{ color: p.payload.fill }}>
        {p.name}
      </p>
      <p className="text-app-text">{p.value}% of portfolio</p>
    </div>
  );
}

function StackTooltip({
  active,
  payload,
  label,
  fundKeys,
}: {
  active?: boolean;
  payload?: { name: string; value: number; color: string }[];
  label?: string;
  fundKeys: string[];
}) {
  if (!active || !payload?.length) return null;
  const items = fundKeys
    .map((k) => payload.find((p) => p.name === k))
    .filter((p): p is { name: string; value: number; color: string } => !!p && p.value > 0);
  return (
    <div className="rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs shadow-xl">
      <p className="mb-1 font-semibold text-app-text">{label}</p>
      {items.map((p) => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: {p.value}%
        </p>
      ))}
    </div>
  );
}

function ScatterTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: { name: string; risk: number; return1Y: number } }[];
}) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs shadow-xl">
      <p className="font-semibold text-groww">{p.name}</p>
      <p className="text-app-muted">Volatility index: {p.risk}</p>
      <p className="text-app-text">1Y return: {p.return1Y}%</p>
    </div>
  );
}

function RadarTooltip({
  active,
  label,
  payload,
  series,
}: {
  active?: boolean;
  label?: string;
  payload?: { name: string; value: number; color: string }[];
  series: { name: string }[];
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs shadow-xl">
      <p className="mb-1 font-semibold text-app-text">{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  );
}
