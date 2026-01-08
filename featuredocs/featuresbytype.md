Doc4TF pages for [Textus Receptus Text Fabric Dataset](https://github.com/mjredmond/tr-text-fabric/tree/master/data/output/tf) (version dataset Jan 7, 2026)
# Overview features by feature type
Overview by [name](featuresbyname.md), [node type](featuresbynodetype.md), or [data type](featuresbydatatype.md).
## Node

Feature|Datatype|Available on nodes|Description|Examples
---|---|---|---|---
[`after`](after.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |after word feature|` `
[`book`](book.md#readme)|[`String`](featuresbydatatype.md#string)|[`book`](featuresbynodetype.md#book) [`clause`](featuresbynodetype.md#clause) [`wg`](featuresbynodetype.md#wg) [`phrase`](featuresbynodetype.md#phrase) [`w`](featuresbynodetype.md#w) |book name (full)|`Acts` `Colossians` `Ephesians` `Galatians`
[`bookshort`](bookshort.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |bookshort word feature|`LUK` `ACT` `MAT` `JHN`
[`case`](case.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |case word feature|`nominative` `accusative` `genitive` `dative`
[`chapter`](chapter.md#readme)|[`Integer`](featuresbydatatype.md#integer)|[`chapter`](featuresbynodetype.md#chapter) [`clause`](featuresbynodetype.md#clause) [`wg`](featuresbynodetype.md#wg) [`phrase`](featuresbynodetype.md#phrase) [`w`](featuresbynodetype.md#w) |chapter number|`1` `2` `3` `4`
[`clausetype`](clausetype.md#readme)|[`String`](featuresbydatatype.md#string)|[`clause`](featuresbynodetype.md#clause) |clause type|`main` `relative` `content` `nominalized`
[`cls`](cls.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |cls word feature|`verb` `noun` `det` `conj`
[`domain`](domain.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |domain word feature|`092004` `089017` `093001` `033006`
[`function`](function.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`phrase`](featuresbynodetype.md#phrase) |syntactic function of phrase/word group|`Cmpl` `Subj` `Objc` `Pred-Obj`
[`gender`](gender.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |gender word feature|`m` `f` `n`
[`gloss`](gloss.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |gloss word feature|`the` `and, also, likewise` `he, she, it, himself, herself, itself; even, very; same` `(rare)`
[`id`](id.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |id word feature|`n40001001001` `n40001001002` `n40001001003` `n40001001004`
[`lemma`](lemma.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |lemma word feature|`ὁ` `καί` `αὐτός` `σύ`
[`lemmatranslit`](lemmatranslit.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |lemmatranslit word feature|`o` `kai` `autos` `su`
[`ln`](ln.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |ln word feature|`92.24` `89.92` `92.11` `23.50`
[`mood`](mood.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |mood word feature|`indicative` `participle` `infinitive` `imp`
[`morph`](morph.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |morph word feature|`CONJ` `PREP` `ADV` `PRT`
[`normalized`](normalized.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |normalized word feature|`καὶ` `ὁ` `ἐν` `δὲ`
[`num`](num.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |num word feature|`1` `2` `3` `4`
[`number`](number.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |number word feature|`s` `p` `d`
[`otype`](otype.md#readme)|[`String`](featuresbydatatype.md#string)||node type assignment|No values
[`person`](person.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |person word feature|`2` `3` `1`
[`ref`](ref.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |ref word feature|`1CO 10:1!1` `1CO 10:1!10` `1CO 10:1!11` `1CO 10:1!12`
[`rela`](rela.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) |relation to context|`Appo`
[`role`](role.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |role word feature|`adv` `v` `s` `o`
[`rule`](rule.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) |syntactic rule for word group|`PrepNp` `DetNP` `NPofNP` `Conj-CL`
[`source`](source.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |source word feature|`n1904` `nlp`
[`sp`](sp.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |sp word feature|`verb` `subs` `art` `conj`
[`strong`](strong.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |strong word feature|`G3588` `G2532` `G846` `G1161`
[`structure_confidence`](structure_confidence.md#readme)|[`String`](featuresbydatatype.md#string)|[`clause`](featuresbynodetype.md#clause) [`wg`](featuresbynodetype.md#wg) [`phrase`](featuresbynodetype.md#phrase) |confidence score for structure inference (0-1)|`1.00`
[`structure_source`](structure_source.md#readme)|[`String`](featuresbydatatype.md#string)|[`clause`](featuresbynodetype.md#clause) [`wg`](featuresbynodetype.md#wg) [`phrase`](featuresbynodetype.md#phrase) |source of structure (direct/inferred/unknown_only)|`direct`
[`tense`](tense.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |tense word feature|`present` `aorist` `pres` `past`
[`text`](text.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |text word feature|`καὶ` `ὁ` `ἐν` `δὲ`
[`trailer`](trailer.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |trailer word feature|` `
[`trans`](trans.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |trans word feature|`the` `and` `-` `in`
[`translit`](translit.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |translit word feature|`kai` `o` `en` `to`
[`typ`](typ.md#readme)|[`String`](featuresbydatatype.md#string)|[`clause`](featuresbynodetype.md#clause) [`wg`](featuresbynodetype.md#wg) [`phrase`](featuresbynodetype.md#phrase) |syntactic type of phrase/clause|`Voct`
[`typems`](typems.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |typems word feature|`common` `personal` `proper` `demonstrative`
[`unaccent`](unaccent.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |unaccent word feature|`και` `ο` `δε` `εν`
[`unicode`](unicode.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |unicode word feature|`καὶ` `ὁ` `ἐν` `δὲ`
[`verse`](verse.md#readme)|[`Integer`](featuresbydatatype.md#integer)|[`verse`](featuresbynodetype.md#verse) [`clause`](featuresbynodetype.md#clause) [`wg`](featuresbynodetype.md#wg) [`phrase`](featuresbynodetype.md#phrase) [`w`](featuresbynodetype.md#w) |verse number|`1` `2` `3` `4`
[`voice`](voice.md#readme)|[`String`](featuresbydatatype.md#string)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |voice word feature|`active` `act` `passive` `middle`
## Edge

Feature|Datatype|Available on nodes|Description|Examples
---|---|---|---|---
[`oslots`](oslots.md#readme)|[`String`](featuresbydatatype.md#string)||slot containment for non-slot nodes|No values
[`parent`](parent.md#readme)|[`Integer`](featuresbydatatype.md#integer)|[`wg`](featuresbynodetype.md#wg) [`w`](featuresbynodetype.md#w) |parent (head) word in dependency tree|`Link`


Created on Jan. 08, 2026 using [Doc4TF version 0.5.2 (July 10, 2024)](https://github.com/tonyjurg/Doc4TF/blob/main/CreateFeatureDoc.ipynb)