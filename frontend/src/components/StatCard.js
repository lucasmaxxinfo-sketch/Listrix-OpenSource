export const StatCard = ({ label, value, icon: Icon, accent }) => {
  return (
    <div className="rounded-xl border border-border bg-card/60 p-4 shadow-panelSoft">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
        {Icon && (
          <span className={`flex h-7 w-7 items-center justify-center rounded-lg ${accent ? "bg-[rgba(255,122,26,0.12)] text-primary" : "bg-muted/40 text-muted-foreground"}`}>
            <Icon size={15} />
          </span>
        )}
      </div>
      <p className="text-2xl font-semibold tabular-nums">{value}</p>
    </div>
  );
};

export default StatCard;
