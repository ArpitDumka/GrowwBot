"use client";

import { useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { growthSeries, navSeries } from "@/lib/marketInsights/mockData";
import type { CompareMetric, FundSnapshot, NavPeriod } from "@/lib/marketInsights/types";
import { useInsights } from "@/lib/insights/useInsights";
import { GlassCard } from "./GlassCard";
import { InsightsPageHeader } from "./InsightsPageHeader";

const PERIODS: NavPeriod[] = ["1M", "6M", "1Y", "3Y", "5Y"];
const CHART_GRID = "#2A3444";
const CHART_AXIS = "#8B95A8";
const ACCENT = "#00D09C";

type Props = {
  onBack: () => void;
  onMenuClick?: () => void;
  showMenu?: boolean;
};

export function MarketInsightsPage({ onBack, onMenuClick, showMenu }: Props) {
  const { funds, marketFacts, disclaimer, lastUpdated, loading, fromApi, error } = useInsights();
  const [fundId, setFundId] = useState(funds[0]?.id ?? "midcap");
  const [period, setPeriod] = useState<NavPeriod>("1Y");
  const [compareMetric, setCompareMetric] = useState<CompareMetric>("expenseRatio");

  const fund = funds.find((f) => f.id === fundId) ?? funds[0];
  const lineData = useMemo(() => (fund ? navSeries(fundId, period, fund.nav) : []), [fundId, period, fund]);
  const areaData = useMemo(() => (fund ? growthSeries(fundId, fund.nav) : []), [fundId, fund]);

  const barData = useMemo(
    () =>
      funds.map((f) => ({
        name: f.shortName,
        value:
          compareMetric === "expenseRatio"
            ? f.expenseRatio
            : compareMetric === "aumCr"
              ? f.aumCr
              : f.returns["1Y"] ?? 0,
      })),
    [compareMetric, funds]
  );

  if (loading || !fund) {
    return (
      <div className="flex min-h-0 flex-1 flex-col items-center justify-center text-app-muted">
        Loading market insights…
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <InsightsPageHeader
        title="Market Insights"
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
          <FundPicker funds={funds} selected={fundId} onSelect={setFundId} />
          <SummaryCards fund={fund} />
          <ChartsSection
            fund={fund}
            period={period}
            onPeriod={setPeriod}
            lineData={lineData}
            areaData={areaData}
            barData={barData}
            compareMetric={compareMetric}
            onCompareMetric={setCompareMetric}
          />
          <div className="grid gap-6 lg:grid-cols-2">
            <FundInfoPanel fund={fund} />
            <MarketFactsFeed facts={marketFacts} />
          </div>
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
    <Panel className="space-y-1 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100/90">
      <p>{text}</p>
      {fromApi && lastUpdated ? (
        <p className="text-xs text-amber-200/70">Scheme facts last updated: {lastUpdated}</p>
      ) : null}
      {apiError ? <p className="text-xs text-amber-200/60">API unavailable — showing fallback data.</p> : null}
    </Panel>
  );
}

function FundPicker({
  funds,
  selected,
  onSelect,
}: {
  funds: FundSnapshot[];
  selected: string;
  onSelect: (id: string) => void;
}) {
  return (
    <Panel className="flex flex-wrap gap-2">
      {funds.map((f) => (
        <button
          key={f.id}
          type="button"
          onClick={() => onSelect(f.id)}
          className={`rounded-full px-3 py-1.5 text-xs font-medium transition sm:text-sm ${
            selected === f.id
              ? "bg-groww text-app-bg shadow-md shadow-groww/20"
              : "border border-app-border bg-app-surface/80 text-app-muted hover:border-groww/40 hover:text-app-text"
          }`}
        >
          {f.shortName}
        </button>
      ))}
    </Panel>
  );
}

function SummaryCards({ fund }: { fund: FundSnapshot }) {
  const items = [
    { label: "NAV", value: `₹${fund.nav.toFixed(2)}` },
    { label: "Expense Ratio", value: `${fund.expenseRatio}%` },
    { label: "AUM", value: `₹${fund.aumCr.toLocaleString("en-IN")} Cr` },
    { label: "Riskometer", value: fund.risk },
    { label: "Category", value: fund.category },
    { label: "Benchmark", value: fund.benchmark },
    { label: "Fund Manager", value: fund.manager },
  ];

  return (
    <section>
      <SectionTitle>Fund snapshot</SectionTitle>
      <Panel className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {items.map((item) => (
          <GlassCard key={item.label}>
            <p className="text-xs font-medium uppercase tracking-wide text-app-muted">{item.label}</p>
            <p className="mt-2 text-lg font-semibold text-app-text">{item.value}</p>
          </GlassCard>
        ))}
      </Panel>
    </section>
  );
}

function ChartsSection({
  fund,
  period,
  onPeriod,
  lineData,
  areaData,
  barData,
  compareMetric,
  onCompareMetric,
}: {
  fund: FundSnapshot;
  period: NavPeriod;
  onPeriod: (p: NavPeriod) => void;
  lineData: { date: string; nav: number }[];
  areaData: { date: string; nav: number }[];
  barData: { name: string; value: number }[];
  compareMetric: CompareMetric;
  onCompareMetric: (m: CompareMetric) => void;
}) {
  return (
    <section className="space-y-6">
      <SectionTitle>Interactive charts</SectionTitle>
      <Panel className="grid gap-6 xl:grid-cols-2">
        <GlassCard>
          <ChartHeader title="NAV trend" subtitle={`${fund.name} · historical (mock)`} />
          <PeriodToggle period={period} onPeriod={onPeriod} />
          <ChartBox height={280}>
            <LineChart data={lineData}>
              <CartesianGrid stroke={CHART_GRID} strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fill: CHART_AXIS, fontSize: 10 }} tickFormatter={(v) => v.slice(5)} />
              <YAxis tick={{ fill: CHART_AXIS, fontSize: 10 }} domain={["auto", "auto"]} />
              <Tooltip content={<DarkTooltip suffix="" prefix="₹" />} />
              <Line type="monotone" dataKey="nav" stroke={ACCENT} strokeWidth={2} dot={false} />
            </LineChart>
          </ChartBox>
        </GlassCard>

        <GlassCard>
          <ChartHeader title="Historical growth" subtitle="Indexed growth % (mock 5Y)" />
          <ChartBox height={280}>
            <AreaChart data={areaData}>
              <defs>
                <linearGradient id="growthGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={ACCENT} stopOpacity={0.45} />
                  <stop offset="100%" stopColor={ACCENT} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke={CHART_GRID} strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fill: CHART_AXIS, fontSize: 10 }} tickFormatter={(v) => v.slice(0, 4)} />
              <YAxis tick={{ fill: CHART_AXIS, fontSize: 10 }} unit="%" />
              <Tooltip content={<DarkTooltip suffix="%" />} />
              <Area type="monotone" dataKey="nav" stroke={ACCENT} fill="url(#growthGrad)" />
            </AreaChart>
          </ChartBox>
        </GlassCard>

        <GlassCard>
          <ChartHeader title="Cross-fund comparison" subtitle="Factual metrics across indexed schemes" />
          <CompareToggle metric={compareMetric} onMetric={onCompareMetric} />
          <ChartBox height={280}>
            <BarChart data={barData} layout="vertical" margin={{ left: 8 }}>
              <CartesianGrid stroke={CHART_GRID} strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={{ fill: CHART_AXIS, fontSize: 10 }} />
              <YAxis type="category" dataKey="name" width={72} tick={{ fill: CHART_AXIS, fontSize: 10 }} />
              <Tooltip content={<DarkTooltip suffix={compareMetric === "aumCr" ? " Cr" : compareMetric === "expenseRatio" ? "%" : "%"} />} />
              <Bar dataKey="value" fill={ACCENT} radius={[0, 6, 6, 0]} />
            </BarChart>
          </ChartBox>
        </GlassCard>

        <GlassCard>
          <ChartHeader title="Sector exposure heatmap" subtitle={`${fund.shortName} · allocation % (mock)`} />
          <SectorHeatmap sectors={fund.sectors} />
        </GlassCard>
      </Panel>
    </section>
  );
}

function SectorHeatmap({ sectors }: { sectors: Record<string, number> }) {
  const max = Math.max(...Object.values(sectors));
  return (
    <Panel className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
      {Object.entries(sectors).map(([name, pct]) => {
        const intensity = pct / max;
        return (
          <Panel
            key={name}
            className="rounded-xl border border-white/5 p-3 text-center transition hover:scale-[1.02]"
            style={{
              backgroundColor: `rgba(0, 208, 156, ${0.08 + intensity * 0.35})`,
            }}
          >
            <p className="text-xs text-app-muted">{name}</p>
            <p className="mt-1 text-lg font-semibold text-app-text">{pct}%</p>
          </Panel>
        );
      })}
    </Panel>
  );
}

function FundInfoPanel({ fund }: { fund: FundSnapshot }) {
  const rows = [
    ["Category definition", fund.categoryDefinition],
    ["Lock-in period", fund.lockIn ?? "None"],
    ["Benchmark", fund.benchmark],
    ["Risk level", fund.risk],
    ["Exit load", fund.exitLoad],
    ["Investment objective", fund.objective],
  ];

  return (
    <GlassCard className="h-full">
      <SectionTitle>Fund information</SectionTitle>
      <dl className="mt-4 space-y-4">
        {rows.map(([label, value]) => (
          <Panel key={label}>
            <dt className="text-xs font-semibold uppercase tracking-wide text-groww/80">{label}</dt>
            <dd className="mt-1 text-sm leading-relaxed text-app-text/90">{value}</dd>
          </Panel>
        ))}
      </dl>
    </GlassCard>
  );
}

function MarketFactsFeed({ facts }: { facts: import("@/lib/marketInsights/types").MarketFact[] }) {
  return (
    <GlassCard className="h-full">
      <SectionTitle>Market facts feed</SectionTitle>
      <p className="mt-1 text-xs text-app-muted">Informational updates only — not trading signals.</p>
      <ul className="mt-4 space-y-3">
        {facts.map((fact) => (
          <li
            key={fact.id}
            className="rounded-xl border border-app-border/60 bg-app-bg/40 p-4 transition hover:border-groww/30"
          >
            <Panel className="flex flex-wrap items-center gap-2 text-xs text-app-muted">
              <span className="rounded-full bg-groww/15 px-2 py-0.5 font-medium text-groww">{fact.tag}</span>
              <span>{fact.time}</span>
            </Panel>
            <p className="mt-2 font-medium text-app-text">{fact.title}</p>
            <p className="mt-1 text-sm text-app-muted">{fact.body}</p>
          </li>
        ))}
      </ul>
    </GlassCard>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h3 className="text-base font-semibold text-app-text">{children}</h3>;
}

function ChartHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <Panel className="mb-3">
      <p className="font-semibold text-app-text">{title}</p>
      <p className="text-xs text-app-muted">{subtitle}</p>
    </Panel>
  );
}

function PeriodToggle({ period, onPeriod }: { period: NavPeriod; onPeriod: (p: NavPeriod) => void }) {
  return (
    <Panel className="mb-3 flex flex-wrap gap-1">
      {PERIODS.map((p) => (
        <button
          key={p}
          type="button"
          onClick={() => onPeriod(p)}
          className={`rounded-md px-2.5 py-1 text-xs font-medium ${
            period === p ? "bg-groww/20 text-groww" : "text-app-muted hover:bg-app-surface"
          }`}
        >
          {p}
        </button>
      ))}
    </Panel>
  );
}

function CompareToggle({
  metric,
  onMetric,
}: {
  metric: CompareMetric;
  onMetric: (m: CompareMetric) => void;
}) {
  const opts: { id: CompareMetric; label: string }[] = [
    { id: "expenseRatio", label: "Expense ratio" },
    { id: "aumCr", label: "AUM" },
    { id: "return1Y", label: "1Y return" },
  ];
  return (
    <Panel className="mb-3 flex flex-wrap gap-1">
      {opts.map((o) => (
        <button
          key={o.id}
          type="button"
          onClick={() => onMetric(o.id)}
          className={`rounded-md px-2.5 py-1 text-xs font-medium ${
            metric === o.id ? "bg-groww/20 text-groww" : "text-app-muted hover:bg-app-surface"
          }`}
        >
          {o.label}
        </button>
      ))}
    </Panel>
  );
}

function ChartBox({ height, children }: { height: number; children: React.ReactNode }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      {children as React.ReactElement}
    </ResponsiveContainer>
  );
}

function DarkTooltip({
  active,
  payload,
  label,
  suffix = "",
  prefix = "",
}: {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
  suffix?: string;
  prefix?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <Panel className="rounded-lg border border-app-border bg-app-surface px-3 py-2 text-xs shadow-xl">
      <p className="text-app-muted">{label}</p>
      <p className="font-semibold text-groww">
        {prefix}
        {payload[0].value}
        {suffix}
      </p>
    </Panel>
  );
}

function Panel({
  className,
  children,
  style,
}: {
  className?: string;
  children?: React.ReactNode;
  style?: React.CSSProperties;
}) {
  return (
    <div className={className} style={style}>
      {children}
    </div>
  );
}
