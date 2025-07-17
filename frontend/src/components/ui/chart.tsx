"use client"

import * as React from "react"
import { ResponsiveContainer } from "recharts"

import { cn } from "@/lib/utils"

// Chart configuration type
export type ChartConfig = {
    [k in string]: {
        label?: React.ReactNode
        icon?: React.ComponentType
    } & (
        | { color?: string; theme?: never }
        | { color?: never; theme: Record<string, string> }
    )
}

// Chart context
type ChartContextProps = {
    config: ChartConfig
}

const ChartContext = React.createContext<ChartContextProps | null>(null)

function useChart() {
    const context = React.useContext(ChartContext)

    if (!context) {
        throw new Error("useChart must be used within a <ChartContainer />")
    }

    return context
}

// Chart container component
const ChartContainer = React.forwardRef<
    HTMLDivElement,
    React.ComponentProps<"div"> & {
        config: ChartConfig
        children: React.ComponentProps<typeof ResponsiveContainer>["children"]
    }
>(({ id, className, children, config, ...props }, ref) => {
    const uniqueId = React.useId()
    const chartId = `chart-${id || uniqueId.replace(/:/g, "")}`

    return (
        <ChartContext.Provider value={{ config }}>
            <div
                data-chart={chartId}
                ref={ref}
                className={cn(
                    "flex aspect-video justify-center text-xs [&_.recharts-cartesian-axis-tick_text]:fill-muted-foreground [&_.recharts-cartesian-grid_line[stroke='#ccc']]:stroke-border/25 [&_.recharts-curve.recharts-tooltip-cursor]:stroke-border [&_.recharts-dot[stroke='#fff']]:stroke-transparent [&_.recharts-layer]:outline-none [&_.recharts-polar-grid_[stroke='#ccc']]:stroke-border [&_.recharts-radial-bar-background-sector]:fill-muted [&_.recharts-rectangle.recharts-tooltip-cursor]:fill-muted [&_.recharts-reference-line_[stroke='#ccc']]:stroke-border [&_.recharts-sector[stroke='#fff']]:stroke-transparent [&_.recharts-sector]:outline-none [&_.recharts-surface]:outline-none",
                    className
                )}
                {...props}
            >
                <ChartStyle id={chartId} config={config} />
                <ResponsiveContainer>
                    {children}
                </ResponsiveContainer>
            </div>
        </ChartContext.Provider>
    )
})
ChartContainer.displayName = "ChartContainer"

// Chart style component
const ChartStyle = ({ id, config }: { id: string; config: ChartConfig }) => {
    const colorConfig = Object.entries(config).filter(
        ([_, config]) => config.theme || config.color
    )

    if (!colorConfig.length) {
        return null
    }

    return (
        <style
            dangerouslySetInnerHTML={{
                __html: [
                    `[data-chart=${id}] {`,
                    ...colorConfig.map(([key, itemConfig]) => {
                        const color = itemConfig.theme?.light || itemConfig.color
                        return color ? `  --color-${key}: ${color};` : null
                    }),
                    `}`,
                    `.dark [data-chart=${id}] {`,
                    ...colorConfig.map(([key, itemConfig]) => {
                        const color = itemConfig.theme?.dark || itemConfig.color
                        return color ? `  --color-${key}: ${color};` : null
                    }),
                    `}`,
                ].join("\n"),
            }}
        />
    )
}

// Chart tooltip component
const ChartTooltip = React.forwardRef<
    HTMLDivElement,
    React.ComponentProps<"div"> & {
        active?: boolean
        payload?: Array<{
            dataKey: string
            color: string
            value: number | string
            payload: any
        }>
        label?: string
        indicator?: "line" | "dot" | "dashed"
        hideLabel?: boolean
        hideIndicator?: boolean
        labelFormatter?: (label: any, payload: any) => React.ReactNode
        labelClassName?: string
        formatter?: (
            value: any,
            name: any,
            item: any,
            index: any,
            payload: any
        ) => React.ReactNode
    }
>(
    (
        {
            active,
            payload,
            className,
            indicator = "dot",
            hideLabel = false,
            hideIndicator = false,
            label,
            labelFormatter,
            labelClassName,
            formatter,
            color,
            ...props
        },
        ref
    ) => {
        const { config } = useChart()

        const tooltipLabel = React.useMemo(() => {
            if (hideLabel || !payload?.length) {
                return null
            }

            const [item] = payload
            const key = `${labelClassName || item?.dataKey || (item as any)?.name || "value"}`
            const itemConfig = getPayloadConfigFromPayload(config, item, key)
            const value =
                !labelFormatter && item?.payload?.[key]
                    ? item?.payload?.[key]
                    : labelFormatter
                        ? labelFormatter(label, payload)
                        : label

            return (
                <div className={cn("font-medium", labelClassName)}>
                    {value}
                </div>
            )
        }, [
            label,
            labelFormatter,
            payload,
            hideLabel,
            labelClassName,
            config,
        ])

        if (!active || !payload?.length) {
            return null
        }

        const nestLabel = payload.length === 1 && indicator !== "dot"

        return (
            <div
                ref={ref}
                className={cn(
                    "grid min-w-[8rem] items-start gap-1.5 rounded-lg border border-border/50 bg-background px-2.5 py-1.5 text-xs shadow-xl",
                    className
                )}
                {...props}
            >
                {!nestLabel ? tooltipLabel : null}
                <div className="grid gap-1.5">
                    {payload.map((item, index) => {
                        const key = `${item.dataKey || (item as any).name || "value"}`
                        const itemConfig = getPayloadConfigFromPayload(config, item, key)
                        const indicatorColor = color || item.payload.fill || item.color

                        return (
                            <div
                                key={item.dataKey}
                                className={cn(
                                    "flex w-full flex-wrap items-stretch gap-2 [&>svg]:h-2.5 [&>svg]:w-2.5 [&>svg]:text-muted-foreground",
                                    indicator === "dot" && "items-center"
                                )}
                            >
                                {formatter && item?.value !== undefined && (item as any).name ? (
                                    formatter(item.value, (item as any).name, item, index, item.payload)
                                ) : (
                                    <>
                                        {itemConfig?.icon ? (
                                            <itemConfig.icon />
                                        ) : (
                                            !hideIndicator && (
                                                <div
                                                    className={cn(
                                                        "shrink-0 rounded-[2px] border-[--color-border] bg-[--color-bg]",
                                                        {
                                                            "h-2.5 w-2.5": indicator === "dot",
                                                            "w-1": indicator === "line",
                                                            "w-0 border-[1.5px] border-dashed bg-transparent":
                                                                indicator === "dashed",
                                                            "my-0.5": nestLabel && indicator === "dashed",
                                                        }
                                                    )}
                                                    style={
                                                        {
                                                            "--color-bg": indicatorColor,
                                                            "--color-border": indicatorColor,
                                                        } as React.CSSProperties
                                                    }
                                                />
                                            )
                                        )}
                                        <div
                                            className={cn(
                                                "flex flex-1 justify-between leading-none",
                                                nestLabel ? "items-end" : "items-center"
                                            )}
                                        >
                                            <div className="grid gap-1.5">
                                                {nestLabel ? tooltipLabel : null}
                                                <span className="text-muted-foreground">
                                                    {itemConfig?.label || (item as any).name}
                                                </span>
                                            </div>
                                            {item.value && (
                                                <span className="font-mono font-medium tabular-nums text-foreground">
                                                    {item.value.toLocaleString()}
                                                </span>
                                            )}
                                        </div>
                                    </>
                                )}
                            </div>
                        )
                    })}
                </div>
            </div>
        )
    }
)
ChartTooltip.displayName = "ChartTooltip"

// Chart tooltip content component
const ChartTooltipContent = React.forwardRef<
    HTMLDivElement,
    React.ComponentProps<typeof ChartTooltip>
>(({ active, payload, className, indicator = "dot", ...props }, ref) => {
    return (
        <ChartTooltip
            ref={ref}
            active={active}
            payload={payload}
            className={className}
            indicator={indicator}
            {...props}
        />
    )
})
ChartTooltipContent.displayName = "ChartTooltipContent"

// Helper function
function getPayloadConfigFromPayload(
    config: ChartConfig,
    payload: unknown,
    key: string
) {
    if (typeof payload !== "object" || payload === null) {
        return undefined
    }

    const payloadPayload =
        "payload" in payload &&
            typeof payload.payload === "object" &&
            payload.payload !== null
            ? payload.payload
            : undefined

    let configLabelKey: string = key

    if (
        key in config ||
        (payloadPayload && configLabelKey in payloadPayload)
    ) {
        return config[configLabelKey]
    }

    return config[key]
}

export {
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
    ChartStyle,
} 