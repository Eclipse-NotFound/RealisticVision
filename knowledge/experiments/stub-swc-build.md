---
domain: knowledge-validation
type: experiments

game-version:
  - "1.02"

confidence: medium
verified: true

discovered-by: RealisticVision

evidence:
  - kind: runtime-experiment
    summary: "编译产物经 ffdec -dumpAS3 验证仅含 RealisticVisionMod 类，无嵌入 fe.*"

date-updated: 2026-08-15
---

# 模组编译方案：公共 API 存根 SWC + mxmlc（已验证可行）

## 问题

- 游戏 pfe.swf 是 SWF 41（FWS）反编译产物；本机只有 Apache Flex 4.16.1 SDK
  （playerglobal 最高 32.0），其 mxmlc 不接受裸 SWF 作 external library
  （报"不是 SWC 文件"），也编译不出 41。
- 运行时注入模型：模组由补丁 MainFE 以 Loader + 子 ApplicationDomain 加载 →
  模组代码引用的 `fe.*` 会在父域（游戏）解析。因此**编译期只需要类型签名**。

## 方案

1. `build/stubs/` 内手写游戏公共 API 存根（包名/类名/成员签名与游戏一致，
   只含模组用到的成员）。
2. `acompc -include-classes ...` → `build/GameStubs.swc`。
3. `amxmlc -swf-version=32 -external-library-path+=GameStubs.swc` 编译模组 →
   `release/RealisticVisionMod.swf`（文档类 RealisticVisionMod extends Sprite，
   含 `public static function init(main:*):void` —— 游戏调用的是**类上的静态
   init**，不是实例方法）。
4. 验证：`ffdec -dumpAS3` 确认 SWF 只含 RealisticVisionMod 一个类
   （fe.* 为 external 链接，不会嵌入）。

## 注意

- 模组 SWF 32 可被游戏运行时（支持 41）加载——向后兼容。
- 存根只放 build/，绝不随 release 发布（同名类会被子域优先解析，破坏注入）。
- `is`/`as`/静态成员访问经 external 链接在运行时解析到游戏真实类，验证方式：
  运行时 F10 调试面板 + 日志。
