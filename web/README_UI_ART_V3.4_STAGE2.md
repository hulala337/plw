# Pelican Workbench V3.4 — Art Stage 2

本阶段只处理「③ 天气 / 昼夜环境系统」，不改动业务 API、数据结构或统计逻辑。

## 已加入

- 自动读取现有天气文本，分类为 clear / cloud / rain / snow / mist
- 自动读取现有时钟，分类为 dawn / day / dusk / night
- 场景使用 `data-time` / `data-weather` 驱动环境表现
- 白天 / 夜晚插画平滑切换
- 黄昏降低亮度并暖化画面
- 雨天启用雨滴氛围层
- 阴天 / 雾天降低饱和度和亮度
- 夜间增强显示器呼吸式光晕
- 雨滴层使用极慢位移动画，避免明显网页动画感

## 设计原则

天气与时间只影响「表现层」。原有天气 API、时钟、工作统计、TODO、Focus、Replay 等功能没有改写。

## 文件

`web/assets/environment.css` 是本阶段新增文件。

`web/index.html` 只增加一个 presentation layer：读取已有 `#weather`、`#clock` 和 `#scene`，不改变业务函数。
