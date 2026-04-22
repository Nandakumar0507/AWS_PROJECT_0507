from collections import deque


def neighbors(r, c, size=32):
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < size and 0 <= nc < size:
            yield nr, nc


def cluster_sizes(matrix, threshold):
    size = len(matrix)
    visited = [[False] * size for _ in range(size)]
    clusters = []
    for r in range(size):
        for c in range(size):
            if visited[r][c] or matrix[r][c] <= threshold:
                continue
            q = deque([(r, c)])
            visited[r][c] = True
            count = 0
            while q:
                cr, cc = q.popleft()
                count += 1
                for nr, nc in neighbors(cr, cc, size):
                    if not visited[nr][nc] and matrix[nr][nc] > threshold:
                        visited[nr][nc] = True
                        q.append((nr, nc))
            clusters.append(count)
    return clusters


def peak_pressure_index(matrix, noise_threshold=0, min_region=10):
    clusters = cluster_sizes(matrix, noise_threshold)
    if not clusters or max(clusters) < min_region:
        return 0.0
    return float(max(max(row) for row in matrix))


def contact_area_pct(matrix, pressure_threshold=100):
    total = len(matrix) * len(matrix[0])
    active = sum(1 for row in matrix for value in row if value > pressure_threshold)
    return round((active / total) * 100, 2)


def high_pressure_sustained(matrices, high_pressure_threshold=3000, min_cluster_pixels=10, sustained_frames=5):
    streak = 0
    for matrix in matrices:
        clusters = cluster_sizes(matrix, high_pressure_threshold)
        if any(cluster >= min_cluster_pixels for cluster in clusters):
            streak += 1
            if streak >= sustained_frames:
                return True
        else:
            streak = 0
    return False


def severity_for_ppi(ppi):
    if ppi > 3500:
        return "HIGH"
    if ppi > 2500:
        return "MEDIUM"
    return "LOW"
