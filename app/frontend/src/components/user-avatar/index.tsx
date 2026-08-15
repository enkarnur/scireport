import { useEffect, useState } from 'react';
import { Avatar, Popover } from '@arco-design/web-react';
import { useAuth } from '../auth-guard';
import { getJwtWithoutRedirect } from '@/auth';

// ── LarkUser ─────────────────────────────────────────────────────────────────
// 展示飞书用户头像 + 姓名，批量请求字节云 component API，模块级缓存防重复请求

type UserInfo = { name: string; username: string; avatar_url?: string };

const _cache = new Map<string, UserInfo | null>();
const _pending = new Map<string, Array<(u: UserInfo | null) => void>>();
let _timer: ReturnType<typeof setTimeout> | null = null;

function enqueueFetch(username: string): Promise<UserInfo | null> {
  if (_cache.has(username)) return Promise.resolve(_cache.get(username)!);
  return new Promise((resolve) => {
    if (!_pending.has(username)) _pending.set(username, []);
    _pending.get(username)!.push(resolve);
    if (!_timer) {
      _timer = setTimeout(async () => {
        _timer = null;
        const usernames = [..._pending.keys()];
        const resolvers = new Map(_pending);
        _pending.clear();
        try {
          const jwt = await getJwtWithoutRedirect();
          if (!jwt) throw new Error('JWT unavailable');
          const query = new URLSearchParams({ usernames: usernames.join(',') });
          const res = await fetch(
            `https://cloud.bytedance.net/api/v1/cloud/component/api/v1/user?${query}`,
            { headers: { 'x-jwt-token': jwt } }
          );
          const data = await res.json();
          const items: UserInfo[] = data?.data?.items ?? [];
          const byName = new Map(items.map((u) => [u.username, u]));
          for (const un of usernames) {
            const u = byName.get(un) ?? null;
            _cache.set(un, u);
            resolvers.get(un)?.forEach((fn) => fn(u));
          }
        } catch {
          for (const un of usernames) {
            _cache.set(un, null);
            resolvers.get(un)?.forEach((fn) => fn(null));
          }
        }
      }, 0);
    }
  });
}

const SIZE = { mini: 20, small: 24, default: 28, large: 44 } as const;
const FS = { mini: 10, small: 11, default: 12, large: 16 } as const;

function IdentityAvatar({
  src,
  label,
  size,
}: {
  src?: string;
  label: string;
  size: number;
}) {
  const initial = label[0]?.toUpperCase() || '?';
  return (
    <Avatar
      size={size}
      style={src ? undefined : {
        backgroundColor: 'var(--aime-color-fill-brand-default)',
        color: 'var(--aime-color-text-white)',
      }}
    >
      {src ? <img src={src} alt={label} width={size} height={size} /> : initial}
    </Avatar>
  );
}

export function LarkUser({
  username,
  size = 'default',
  showUsername = false,
}: {
  username: string;
  size?: keyof typeof SIZE;
  showUsername?: boolean;
}) {
  const normalizedUsername = username.trim();
  const [info, setInfo] = useState<UserInfo | null>(() => _cache.get(normalizedUsername) ?? null);
  const px = SIZE[size];
  const fs = FS[size];

  useEffect(() => {
    if (!normalizedUsername) {
      setInfo(null);
      return undefined;
    }
    let cancelled = false;
    enqueueFetch(normalizedUsername).then((u) => { if (!cancelled) setInfo(u); });
    return () => { cancelled = true; };
  }, [normalizedUsername]);

  if (!normalizedUsername) return null;

  const displayName = info?.name || normalizedUsername;

  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, minWidth: 0, maxWidth: '100%' }}>
      <IdentityAvatar src={info?.avatar_url} label={displayName} size={px} />
      <span style={{ minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: fs + 1, color: 'var(--aime-color-text-base-1)' }}>{displayName}</span>
      {showUsername && info?.name && (
        <span style={{ minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: fs, color: 'var(--aime-color-text-base-3)' }}>({normalizedUsername})</span>
      )}
    </span>
  );
}

export function UserAvatar() {
  const { user } = useAuth();

  if (!user) return null;

  const displayName = user.username || user.email || user.user || 'U';
  const profile = (
    <div className="flex min-w-[180px] items-center gap-3 py-1">
      <IdentityAvatar src={user.avatar_url} label={displayName} size={40} />
      <div className="min-w-0">
        <div className="truncate text-sm font-medium" style={{ color: 'var(--aime-color-text-base-1)' }}>
          {displayName}
        </div>
        {user.email && (
          <div className="truncate text-xs" style={{ color: 'var(--aime-color-text-base-3)' }}>
            {user.email}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <Popover content={profile} trigger="click" position="br">
      <button
        type="button"
        aria-label={displayName}
        className="flex items-center gap-2 rounded-md px-2 py-1.5 transition-colors hover:bg-[var(--aime-color-bg-overlay-1)]"
      >
        <IdentityAvatar src={user.avatar_url} label={displayName} size={28} />
        <span
          className="text-sm hidden sm:inline"
          style={{ color: 'var(--aime-color-text-base-1)' }}
        >
          {displayName}
        </span>
      </button>
    </Popover>
  );
}

export default UserAvatar;
