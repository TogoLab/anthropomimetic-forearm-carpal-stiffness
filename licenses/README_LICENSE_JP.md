# License Guide (日本語)

本リポジトリは、複数のライセンスを組み合わせて構成されています。
使用する際は、対象ファイルに適用されるライセンスを必ず確認してください。

## 骨（人体）モデル
- 対象: `cad/bone_*` , `stl/bone_*` ——ただし `bone_ellipsoidal_carpal_*` は**除く**（次節を参照）
- ライセンス: Creative Commons Attribution-ShareAlike 2.1 Japan (CC BY-SA 2.1 JP)
- 原データ出典: BodyParts3D／ライフサイエンス統合データベースセンター, https://lifesciencedb.jp/bp3d/
- 注意:
   - クレジット表示が必要です（例: 論文の引用または本リポジトリURL）
   - 改変・再配布時は同一ライセンス（継承）が必要です
   - 近位手根骨列を融合した部品（`bone_fixed_carpal_proximal`, `bone_fixed_carpal_distal`）は、解剖学的手根骨をCAD上で結合した二次的著作物のため、本節に含まれます

## オリジナル設計部品（楕円体骨格・モータタワー・治具など）
- 対象: `cad/bone_ellipsoidal_carpal_*` , `cad/jig_*` , `cad/exp_*` , `cad/tower_*` , `cad/soft_tissue_*` および `stl/` の対応ファイル
- ライセンス: Creative Commons Attribution 4.0 International (CC BY 4.0)
- 注意:
   - クレジット表示が必要です（例: 論文の引用または本リポジトリURL）
   - 改変・商用利用も可能です
   - 幾何学的楕円体骨格は著者らによるオリジナル設計であり、BodyParts3Dのデータを含みません

## 制御ファームウェア
- 対象: `firmware/*`
- ライセンス: Creative Commons Attribution 4.0 International (CC BY 4.0)
- 注意:
   - クレジット表示が必要です（例: 論文の引用または本リポジトリURL）

## 実験データ・解析コード
- 対象: `analysis/*`
- ライセンス: Creative Commons Attribution 4.0 International (CC BY 4.0)
- 注意:
   - クレジット表示が必要です（例: 論文の引用または本リポジトリURL）

## 動画（media）
- 対象: `media/*`
- ライセンス: Creative Commons Attribution 4.0 International (CC BY 4.0)
- 注意:
   - クレジット表示が必要です（例: 論文の引用または本リポジトリURL）
