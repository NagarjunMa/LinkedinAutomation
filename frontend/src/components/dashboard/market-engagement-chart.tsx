"use client";

import React, { useState, useMemo } from 'react';
import { BentoCard } from './bento-card';
import { Area, AreaChart, CartesianGrid, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";

// Data provided by user
const chartData = [
    { date: "2024-04-01", desktop: 222, mobile: 150 },
    { date: "2024-04-02", desktop: 97, mobile: 180 },
    { date: "2024-04-03", desktop: 167, mobile: 120 },
    { date: "2024-04-04", desktop: 242, mobile: 260 },
    { date: "2024-04-05", desktop: 373, mobile: 290 },
    { date: "2024-04-06", desktop: 301, mobile: 340 },
    { date: "2024-04-07", desktop: 245, mobile: 180 },
    { date: "2024-04-08", desktop: 409, mobile: 320 },
    { date: "2024-04-09", desktop: 59, mobile: 110 },
    { date: "2024-04-10", desktop: 261, mobile: 190 },
    { date: "2024-04-11", desktop: 327, mobile: 350 },
    { date: "2024-04-12", desktop: 292, mobile: 210 },
    { date: "2024-04-13", desktop: 342, mobile: 380 },
    { date: "2024-04-14", desktop: 137, mobile: 220 },
    { date: "2024-04-15", desktop: 120, mobile: 170 },
    { date: "2024-04-16", desktop: 138, mobile: 190 },
    { date: "2024-04-17", desktop: 446, mobile: 360 },
    { date: "2024-04-18", desktop: 364, mobile: 410 },
    { date: "2024-04-19", desktop: 243, mobile: 180 },
    { date: "2024-04-20", desktop: 89, mobile: 150 },
    { date: "2024-04-21", desktop: 137, mobile: 200 },
    { date: "2024-04-22", desktop: 224, mobile: 170 },
    { date: "2024-04-23", desktop: 138, mobile: 230 },
    { date: "2024-04-24", desktop: 387, mobile: 290 },
    { date: "2024-04-25", desktop: 215, mobile: 250 },
    { date: "2024-04-26", desktop: 75, mobile: 130 },
    { date: "2024-04-27", desktop: 383, mobile: 420 },
    { date: "2024-04-28", desktop: 122, mobile: 180 },
    { date: "2024-04-29", desktop: 315, mobile: 240 },
    { date: "2024-04-30", desktop: 454, mobile: 380 },
    { date: "2024-05-01", desktop: 165, mobile: 220 },
    { date: "2024-05-02", desktop: 293, mobile: 310 },
    { date: "2024-05-03", desktop: 247, mobile: 190 },
    { date: "2024-05-04", desktop: 385, mobile: 420 },
    { date: "2024-05-05", desktop: 481, mobile: 390 },
    { date: "2024-05-06", desktop: 498, mobile: 520 },
    { date: "2024-05-07", desktop: 388, mobile: 300 },
    { date: "2024-05-08", desktop: 149, mobile: 210 },
    { date: "2024-05-09", desktop: 227, mobile: 180 },
    { date: "2024-05-10", desktop: 293, mobile: 330 },
    { date: "2024-05-11", desktop: 335, mobile: 270 },
    { date: "2024-05-12", desktop: 197, mobile: 240 },
    { date: "2024-05-13", desktop: 197, mobile: 160 },
    { date: "2024-05-14", desktop: 448, mobile: 490 },
    { date: "2024-05-15", desktop: 473, mobile: 380 },
    { date: "2024-05-16", desktop: 338, mobile: 400 },
    { date: "2024-05-17", desktop: 499, mobile: 420 },
    { date: "2024-05-18", desktop: 315, mobile: 350 },
    { date: "2024-05-19", desktop: 235, mobile: 180 },
    { date: "2024-05-20", desktop: 177, mobile: 230 },
    { date: "2024-05-21", desktop: 82, mobile: 140 },
    { date: "2024-05-22", desktop: 81, mobile: 120 },
    { date: "2024-05-23", desktop: 252, mobile: 290 },
    { date: "2024-05-24", desktop: 294, mobile: 220 },
    { date: "2024-05-25", desktop: 201, mobile: 250 },
    { date: "2024-05-26", desktop: 213, mobile: 170 },
    { date: "2024-05-27", desktop: 420, mobile: 460 },
    { date: "2024-05-28", desktop: 233, mobile: 190 },
    { date: "2024-05-29", desktop: 78, mobile: 130 },
    { date: "2024-05-30", desktop: 340, mobile: 280 },
    { date: "2024-05-31", desktop: 178, mobile: 230 },
    { date: "2024-06-01", desktop: 178, mobile: 200 },
    { date: "2024-06-02", desktop: 470, mobile: 410 },
    { date: "2024-06-03", desktop: 103, mobile: 160 },
    { date: "2024-06-04", desktop: 439, mobile: 380 },
    { date: "2024-06-05", desktop: 88, mobile: 140 },
    { date: "2024-06-06", desktop: 294, mobile: 250 },
    { date: "2024-06-07", desktop: 323, mobile: 370 },
    { date: "2024-06-08", desktop: 385, mobile: 320 },
    { date: "2024-06-09", desktop: 438, mobile: 480 },
    { date: "2024-06-10", desktop: 155, mobile: 200 },
    { date: "2024-06-11", desktop: 92, mobile: 150 },
    { date: "2024-06-12", desktop: 492, mobile: 420 },
    { date: "2024-06-13", desktop: 81, mobile: 130 },
    { date: "2024-06-14", desktop: 426, mobile: 380 },
    { date: "2024-06-15", desktop: 307, mobile: 350 },
    { date: "2024-06-16", desktop: 371, mobile: 310 },
    { date: "2024-06-17", desktop: 475, mobile: 520 },
    { date: "2024-06-18", desktop: 107, mobile: 170 },
    { date: "2024-06-19", desktop: 341, mobile: 290 },
    { date: "2024-06-20", desktop: 408, mobile: 450 },
    { date: "2024-06-21", desktop: 169, mobile: 210 },
    { date: "2024-06-22", desktop: 317, mobile: 270 },
    { date: "2024-06-23", desktop: 480, mobile: 530 },
    { date: "2024-06-24", desktop: 132, mobile: 180 },
    { date: "2024-06-25", desktop: 141, mobile: 190 },
    { date: "2024-06-26", desktop: 434, mobile: 380 },
    { date: "2024-06-27", desktop: 448, mobile: 490 },
    { date: "2024-06-28", desktop: 149, mobile: 200 },
    { date: "2024-06-29", desktop: 103, mobile: 160 },
    { date: "2024-06-30", desktop: 446, mobile: 400 },
];

export const ChartAreaInteractive = () => {
    const [timeRange, setTimeRange] = useState("90d");

    const filteredData = useMemo(() => {
        const referenceDate = new Date("2024-06-30");
        let daysToSubtract = 90;
        if (timeRange === "30d") daysToSubtract = 30;
        else if (timeRange === "7d") daysToSubtract = 7;

        const startDate = new Date(referenceDate);
        startDate.setDate(startDate.getDate() - daysToSubtract);

        return chartData.filter(item => new Date(item.date) >= startDate);
    }, [timeRange]);

    return (
        <BentoCard
            title="Total Market Engagement"
            action={
                <div className="flex gap-1 border border-[#3b3b3b]/5 p-0.5">
                    {["7d", "30d", "90d"].map(range => (
                        <button
                            key={range}
                            onClick={() => setTimeRange(range)}
                            className={`px-3 py-1.5 text-[9px] font-bold uppercase tracking-widest transition-all duration-700 ${timeRange === range ? 'bg-[#3b3b3b] text-white' : 'text-[#3b3b3b]/30 hover:text-[#3b3b3b]/60'}`}
                        >
                            {range === '7d' ? '7 Days' : range === '30d' ? '30 Days' : '3 Months'}
                        </button>
                    ))}
                </div>
            }
            className="col-span-12"
        >
            <div className="space-y-4">
                <div className="flex justify-between items-start">
                    <div className="space-y-1">
                        <h2 className="text-4xl font-mono font-medium">1,248</h2>
                        <p className="text-[10px] text-[#3b3b3b]/40 uppercase tracking-[0.2em]">Total Visitors (Last {timeRange === '90d' ? '90' : timeRange === '30d' ? '30' : '7'} days)</p>
                    </div>
                    <div className="text-right flex gap-8">
                        <div>
                            <p className="text-lg font-mono font-medium">842</p>
                            <p className="text-[8px] text-[#3b3b3b]/40 uppercase font-bold">Desktop</p>
                        </div>
                        <div>
                            <p className="text-lg font-mono font-medium">406</p>
                            <p className="text-[8px] text-[#3b3b3b]/40 uppercase font-bold">Mobile</p>
                        </div>
                    </div>
                </div>

                <div className="w-full h-80 pt-8">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={filteredData}>
                            <defs>
                                <linearGradient id="fillDesktop" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3b3b3b" stopOpacity={0.15} />
                                    <stop offset="95%" stopColor="#3b3b3b" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="fillMobile" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3b3b3b" stopOpacity={0.05} />
                                    <stop offset="95%" stopColor="#3b3b3b" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid vertical={false} stroke="#3b3b3b" strokeOpacity={0.05} strokeDasharray="3 3" />
                            <XAxis
                                dataKey="date"
                                tickLine={false}
                                axisLine={false}
                                tick={{ fontSize: 9, fill: '#3b3b3b', opacity: 0.3, fontFamily: 'JetBrains Mono' }}
                                tickMargin={16}
                                tickFormatter={(val) => new Date(val).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                            />
                            <YAxis hide />
                            <Tooltip
                                cursor={{ stroke: '#3b3b3b', strokeOpacity: 0.1, strokeWidth: 1 }}
                                contentStyle={{
                                    backgroundColor: 'white',
                                    border: '1px solid rgba(59, 59, 59, 0.1)',
                                    fontSize: '10px',
                                    fontFamily: 'JetBrains Mono',
                                    borderRadius: '0px'
                                }}
                                labelFormatter={(val) => new Date(val).toLocaleDateString("en-US", { month: "long", day: "numeric" })}
                            />
                            <Area
                                type="natural"
                                dataKey="mobile"
                                stroke="#3b3b3b"
                                strokeWidth={1}
                                strokeOpacity={0.1}
                                fillOpacity={1}
                                fill="url(#fillMobile)"
                                stackId="1"
                            />
                            <Area
                                type="natural"
                                dataKey="desktop"
                                stroke="#3b3b3b"
                                strokeWidth={2}
                                fillOpacity={1}
                                fill="url(#fillDesktop)"
                                stackId="1"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </BentoCard>
    );
};
