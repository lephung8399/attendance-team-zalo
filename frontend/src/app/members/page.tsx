"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { createMember, listMembers, updateMember } from "@/lib/api";
import { SKILL_LABEL, type Member, type SkillLevel } from "@/lib/types";
import { Button, Card, EmptyState, Field, SkillBadge, inputClass } from "@/components/ui";

const SKILL_OPTIONS: SkillLevel[] = ["GIOI", "TRUNG_BINH", "YEU", "UNKNOWN"];

export default function MembersPage() {
  const queryClient = useQueryClient();
  const membersQuery = useQuery({ queryKey: ["members"], queryFn: listMembers });
  const [name, setName] = useState("");
  const [skill, setSkill] = useState<SkillLevel>("UNKNOWN");

  const createMutation = useMutation({
    mutationFn: () => createMember({ display_name: name, skill_level: skill }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["members"] });
      setName("");
      setSkill("UNKNOWN");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Member> }) => updateMember(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["members"] }),
  });

  const members = membersQuery.data ?? [];
  const active = members.filter((m) => m.status === "ACTIVE");
  const inactive = members.filter((m) => m.status === "INACTIVE");

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Thành viên</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Danh sách thành viên cố định và trình độ — dùng lại cho mọi buổi đá.
        </p>
      </div>

      <Card className="p-5">
        <form
          className="flex flex-wrap items-end gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            if (!name.trim()) return;
            createMutation.mutate();
          }}
        >
          <div className="min-w-[200px] flex-1">
            <Field label="Tên thành viên">
              <input
                className={inputClass}
                placeholder="Nguyễn Văn Minh"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </Field>
          </div>
          <div className="w-44">
            <Field label="Trình độ">
              <select
                className={inputClass}
                value={skill}
                onChange={(e) => setSkill(e.target.value as SkillLevel)}
              >
                {SKILL_OPTIONS.map((s) => (
                  <option key={s} value={s}>
                    {SKILL_LABEL[s]}
                  </option>
                ))}
              </select>
            </Field>
          </div>
          <Button type="submit" variant="primary" disabled={createMutation.isPending}>
            + Thêm
          </Button>
        </form>
      </Card>

      {membersQuery.isLoading ? (
        <p className="text-sm text-muted-foreground">Đang tải…</p>
      ) : members.length === 0 ? (
        <EmptyState title="Chưa có thành viên nào" hint="Thêm thành viên đầu tiên ở trên." />
      ) : (
        <div className="flex flex-col gap-6">
          <MemberList
            title={`Đang hoạt động (${active.length})`}
            members={active}
            onUpdate={(id, data) => updateMutation.mutate({ id, data })}
          />
          {inactive.length > 0 && (
            <MemberList
              title={`Không hoạt động (${inactive.length})`}
              members={inactive}
              onUpdate={(id, data) => updateMutation.mutate({ id, data })}
            />
          )}
        </div>
      )}
    </div>
  );
}

function MemberList({
  title,
  members,
  onUpdate,
}: {
  title: string;
  members: Member[];
  onUpdate: (id: string, data: Partial<Member>) => void;
}) {
  return (
    <div>
      <h2 className="mb-3 text-sm font-medium text-muted-foreground">{title}</h2>
      <Card>
        <ul className="divide-y divide-border">
          {members.map((m) => (
            <li key={m.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
              <div>
                <p className="font-medium">{m.display_name}</p>
                {m.note && <p className="text-xs text-muted-foreground">{m.note}</p>}
              </div>
              <div className="flex items-center gap-2">
                <select
                  className="rounded-full border border-border bg-surface px-2.5 py-1 text-xs"
                  value={m.skill_level}
                  onChange={(e) => onUpdate(m.id, { skill_level: e.target.value as SkillLevel })}
                >
                  {SKILL_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {SKILL_LABEL[s]}
                    </option>
                  ))}
                </select>
                <SkillBadge level={m.skill_level} />
                <button
                  className="text-xs text-muted-foreground underline decoration-dotted hover:text-foreground"
                  onClick={() =>
                    onUpdate(m.id, { status: m.status === "ACTIVE" ? "INACTIVE" : "ACTIVE" })
                  }
                >
                  {m.status === "ACTIVE" ? "Vô hiệu hoá" : "Kích hoạt lại"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
