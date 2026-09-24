"use client";

import {
  CartesianGrid, Legend, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis,
} from "recharts";
import { numero } from "@/src/lib/formato";

export type Grupo = { nome: string; cor: string; pontos: { x: number; y: number }[] };

export function Dispersao({
  grupos, rotuloX, rotuloY, altura = 380,
}: {
  grupos: Grupo[];
  rotuloX: string;
  rotuloY: string;
  altura?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={altura}>
      <ScatterChart margin={{ top: 8, right: 16, bottom: 24, left: 8 }}>
        <CartesianGrid stroke="#ece9e4" />
        <XAxis
          type="number" dataKey="x" name={rotuloX}
          tick={{ fontSize: 12, fill: "#78716c" }} tickLine={false} axisLine={false}
          label={{ value: rotuloX, position: "insideBottom", offset: -12, fontSize: 12, fill: "#78716c" }}
          tickFormatter={(valor) => numero(valor as number, 0)}
        />
        <YAxis
          type="number" dataKey="y" name={rotuloY} width={64}
          tick={{ fontSize: 12, fill: "#78716c" }} tickLine={false} axisLine={false}
          label={{ value: rotuloY, angle: -90, position: "insideLeft", fontSize: 12, fill: "#78716c" }}
          tickFormatter={(valor) => numero(valor as number, 0)}
        />
        <Tooltip formatter={(valor) => numero(valor as number, 0)} cursor={{ strokeDasharray: "3 3" }} />
        {grupos.length > 1 ? <Legend /> : null}
        {grupos.map((grupo) => (
          <Scatter
            key={grupo.nome}
            name={grupo.nome}
            data={grupo.pontos}
            fill={grupo.cor}
            // Ver comentario sobre isAnimationActive em Linha.tsx.
            isAnimationActive={false}
          />
        ))}
      </ScatterChart>
    </ResponsiveContainer>
  );
}
